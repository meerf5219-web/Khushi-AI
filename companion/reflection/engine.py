from __future__ import annotations

"""
Reflection Engine
==================
Generates grounded daily / weekly / monthly reflections from Companion Memory.

Policy:
- Uses ONLY data from the CompanionMemoryStore summary.
- Never invents facts or infers beyond what is explicitly stored.
- Caches the last reflection to avoid redundant disk reads.
- Clearly labels items as: Known / Estimated / Unknown.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


logger = logging.getLogger(__name__)


def _safe_parse_iso(ts: Any) -> Optional[datetime]:
    if not isinstance(ts, str) or not ts:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(ts, fmt)
        except Exception:
            pass
    return None


def _filter_timeline_records(
    timeline_records: List[Dict[str, Any]],
    *,
    freq: str,
    now: Optional[datetime],
) -> List[Dict[str, Any]]:
    if now is None:
        return timeline_records

    valid = []
    for r in timeline_records:
        created = _safe_parse_iso(r.get("created_at"))
        if created is None:
            continue
        rr = dict(r)
        rr["_created_dt"] = created
        valid.append(rr)

    valid.sort(key=lambda x: x["_created_dt"])  # chronological ascending

    if freq == "daily":
        return [r for r in valid if r["_created_dt"].date() == now.date()]
    if freq == "weekly":
        iso_year, iso_week, _ = now.isocalendar()
        return [
            r for r in valid
            if (r["_created_dt"].isocalendar().year, r["_created_dt"].isocalendar().week) == (iso_year, iso_week)
        ]
    if freq == "monthly":
        return [
            r for r in valid
            if r["_created_dt"].year == now.year and r["_created_dt"].month == now.month
        ]
    return valid


def _category_count(items: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count items per category for summary sentences."""
    counts: Dict[str, int] = {}
    for it in items:
        cat = (it.get("category") or "general").strip().lower()
        counts[cat] = counts.get(cat, 0) + 1
    return counts


def _build_natural_summary(items: List[Dict[str, Any]], freq: str) -> str:
    """Generate a human-readable summary from reflection items. No hallucination."""
    if not items:
        return f"No {freq} activity recorded in Companion Memory."

    counts = _category_count(items)

    parts: List[str] = []
    for cat, count in counts.items():
        unit = "entry" if count == 1 else "entries"
        parts.append(f"{count} {cat} {unit}")

    summary = f"This {freq}: " + ", ".join(parts) + "."

    # Surface a few concrete values
    values: List[str] = []
    for it in items[:4]:
        val = it.get("value") or ""
        if val:
            values.append(str(val)[:80])
    if values:
        summary += " Recent: " + "; ".join(values) + "."

    return summary


# ---------------------------------------------------------------------------
# Simple in-process cache for reflections (avoids reprocessing same data)
# ---------------------------------------------------------------------------
@dataclass
class _ReflectionCache:
    summary_hash: int = 0
    now_key: str = ""
    result: Optional[Dict[str, Any]] = None


@dataclass
class ReflectionEngine:
    """
    Reflection generation grounded only in Companion Memory.

    Output structure per frequency:
      {
        "items": [...],        # raw echoed items
        "note": str,           # data provenance note
        "natural_summary": str # human-readable summary sentence(s)
        "categories": {...}    # counts per category
      }
    """

    _cache: _ReflectionCache = field(default_factory=_ReflectionCache)

    def generate(
        self,
        *,
        summary: Dict[str, Any],
        now_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        t0 = time.perf_counter()

        # Determine "now" deterministically.
        now_dt: Optional[datetime] = None
        if isinstance(now_text, str) and now_text.strip():
            now_dt = _safe_parse_iso(now_text.strip())

        # Cache key: hash of summary + now_key
        now_key = now_text or ""
        try:
            summary_hash = hash(str(sorted(str(summary))))
        except Exception:
            summary_hash = id(summary)

        if (
            self._cache.result is not None
            and self._cache.summary_hash == summary_hash
            and self._cache.now_key == now_key
        ):
            elapsed = time.perf_counter() - t0
            logger.debug("ReflectionEngine: cache hit (%.4fs)", elapsed)
            return self._cache.result

        timeline = summary.get("timeline", {}).get("records", [])
        if not isinstance(timeline, list):
            timeline = []

        daily_raw = _filter_timeline_records(timeline, freq="daily", now=now_dt) if now_dt else timeline[:]
        weekly_raw = _filter_timeline_records(timeline, freq="weekly", now=now_dt) if now_dt else timeline[:]
        monthly_raw = _filter_timeline_records(timeline, freq="monthly", now=now_dt) if now_dt else timeline[:]

        def _as_items(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            items = []
            for r in records:
                items.append(
                    {
                        "created_at": r.get("created_at"),
                        "category": r.get("category"),
                        "confidence": r.get("confidence"),
                        "value": r.get("value"),
                    }
                )
            return items

        def _section(freq: str, raw: List[Dict[str, Any]]) -> Dict[str, Any]:
            items = _as_items(raw)
            natural = _build_natural_summary(items, freq)
            note = (
                "Generated from Companion Memory timeline."
                if items
                else f"No {freq} memory items found."
            )
            return {
                "items": items,
                "note": note,
                "natural_summary": natural,
                "categories": _category_count(items),
            }

        result = {
            "daily": _section("daily", daily_raw),
            "weekly": _section("weekly", weekly_raw),
            "monthly": _section("monthly", monthly_raw),
        }

        # Update cache
        self._cache = _ReflectionCache(
            summary_hash=summary_hash,
            now_key=now_key,
            result=result,
        )

        elapsed = time.perf_counter() - t0
        logger.info(
            "ReflectionEngine: generated reflection daily=%d weekly=%d monthly=%d (%.4fs)",
            len(daily_raw), len(weekly_raw), len(monthly_raw), elapsed,
        )
        return result

    def invalidate_cache(self) -> None:
        """Force cache invalidation on next generate() call."""
        self._cache = _ReflectionCache()
        logger.debug("ReflectionEngine: cache invalidated")
