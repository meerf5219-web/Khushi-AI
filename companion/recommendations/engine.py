from __future__ import annotations

"""
Recommendation Engine
======================
Generates personalized, grounded recommendations from Companion Memory only.

Policy:
- Uses ONLY CompanionMemoryStore data.
- Never repeats identical recommendations within the same output or session.
- Every recommendation includes a WHY explanation.
- Covers: UPSC, Coding, Projects, Business, Gym, Reading, Health, Career, Finance.
- Confidence is stated explicitly.
"""

import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from config.companion import DUPLICATE_THRESHOLD


logger = logging.getLogger(__name__)


def _normalize(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def _sig(domain: str, title: str) -> str:
    raw = _normalize(f"{domain}|{title}")
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _extract_bucket_values(summary: Dict[str, Any], bucket: str) -> List[str]:
    """Extract non-deleted string values from a dict-type bucket."""
    records = summary.get(bucket, {}).get("records", {})
    if not isinstance(records, dict):
        return []
    out: List[str] = []
    for rec in records.values():
        if not isinstance(rec, dict):
            continue
        payload = rec.get("payload", {})
        if isinstance(payload, dict) and payload.get("status") == "deleted":
            continue
        val = payload.get("value") or payload.get("text") if isinstance(payload, dict) else None
        if val:
            out.append(str(val))
    return out


@dataclass
class RecommendationEngine:
    """
    Recommendation generation grounded only in Companion Memory.

    Session-level duplicate prevention:
    - Signatures of previously recommended items are tracked per instance.
    - Cross-session persistence is NOT attempted (no external state needed).
    """

    _session_seen: Set[str] = field(default_factory=set)

    def generate(
        self,
        *,
        summary: Dict[str, Any],
        reflection: Dict[str, Any],
        planning: Dict[str, Any],
        history_limit: int,
        duplicate_threshold: float,
    ) -> List[Dict[str, Any]]:
        t0 = time.perf_counter()

        goals = [v for v in _extract_bucket_values(summary, "goals") if v]
        habits = [v for v in _extract_bucket_values(summary, "habits") if v]
        projects = [v for v in _extract_bucket_values(summary, "projects") if v]
        preferences = [v for v in _extract_bucket_values(summary, "preferences") if v]
        education = [v for v in _extract_bucket_values(summary, "education") if v]
        career = [v for v in _extract_bucket_values(summary, "career") if v]
        health = [v for v in _extract_bucket_values(summary, "health") if v]

        all_text = goals + habits + projects + preferences + education + career + health

        # Candidate format: (domain, title, why, confidence)
        candidates: List[Tuple[str, str, str, float]] = []

        # --- UPSC ---
        if any("upsc" in _normalize(x) for x in all_text):
            candidates.append((
                "UPSC",
                "UPSC: 45-minute timed revision + 15-minute error log review",
                "Your Companion Memory contains UPSC-related goals or habits. Timed revision with error log review is a high-yield technique.",
                0.85,
            ))
            candidates.append((
                "UPSC",
                "UPSC: Review Polity and Current Affairs — these are highest-weightage sections",
                "Stored UPSC goal detected. Polity and Current Affairs consistently carry the most marks in Prelims.",
                0.80,
            ))

        # --- Gym / Workout ---
        if any("gym" in _normalize(x) or "workout" in _normalize(x) for x in all_text):
            candidates.append((
                "Gym",
                "Gym: Add 10-minute mobility warmup before your main workout",
                "Your Companion Memory includes gym or workout habits. A mobility warmup reduces injury risk without adding significant time.",
                0.78,
            ))

        # --- Coding / Python / Rust ---
        if any(lang in _normalize(x) for x in all_text for lang in ["python", "coding", "programming", "code"]):
            candidates.append((
                "Coding",
                "Coding: Spend 30 minutes on a focused coding problem or project feature",
                "Your Companion Memory shows a coding preference or habit. Consistent daily practice compounds over time.",
                0.80,
            ))
        if any("rust" in _normalize(x) for x in all_text):
            candidates.append((
                "Coding",
                "Coding (Rust): Work on ownership/borrowing examples — the hardest but most important Rust concept",
                "Rust is stored in your preferences. Ownership and borrowing are the highest-value learning areas for Rust beginners.",
                0.75,
            ))

        # --- Projects ---
        if projects:
            for proj in projects[:2]:
                candidates.append((
                    "Projects",
                    f"Project '{proj[:50]}': Write a 3-step execution plan for your next action",
                    f"'{proj[:50]}' is stored in your Companion Memory projects. Breaking next actions into 3 concrete steps reduces friction.",
                    0.82,
                ))

        # --- Reading ---
        if any("read" in _normalize(x) or "book" in _normalize(x) for x in all_text):
            candidates.append((
                "Reading",
                "Reading: Dedicate 20 minutes to your current book — consistent reading builds faster comprehension",
                "A reading-related habit or preference is in your Companion Memory. 20 minutes daily accumulates ~12 books per year.",
                0.72,
            ))

        # --- Health ---
        if health or any("health" in _normalize(x) or "sleep" in _normalize(x) or "diet" in _normalize(x) for x in all_text):
            candidates.append((
                "Health",
                "Health: Track your sleep and hydration today — these directly impact cognitive performance",
                "Health data or habits are stored in your Companion Memory. Sleep and hydration are leading factors in study/work performance.",
                0.70,
            ))

        # --- Career ---
        if career:
            candidates.append((
                "Career",
                f"Career: Review your career goal — '{career[0][:60]}' — and identify one concrete next step",
                "A career goal is stored in your Companion Memory. Reviewing goals weekly maintains alignment and momentum.",
                0.76,
            ))

        # --- Finance ---
        if any("finance" in _normalize(x) or "money" in _normalize(x) or "budget" in _normalize(x) for x in all_text):
            candidates.append((
                "Finance",
                "Finance: Update your budget tracker or savings log — visibility drives better financial decisions",
                "Finance-related information is in your Companion Memory. Regular tracking is the single best habit for financial health.",
                0.68,
            ))

        # --- Business ---
        if any("business" in _normalize(x) or "startup" in _normalize(x) or "entrepreneur" in _normalize(x) for x in all_text):
            candidates.append((
                "Business",
                "Business: Spend 15 minutes on your business idea — write one problem/solution statement",
                "A business-related goal is in your Companion Memory. Articulating the problem you solve is the most important first step.",
                0.74,
            ))

        # --- Fallback ---
        if not candidates and all_text:
            candidates.append((
                "General",
                "Take one small action: pick the easiest next step from your current goals",
                "You have stored goals, habits, or projects in Companion Memory. Starting with the smallest action builds consistency.",
                0.60,
            ))

        # Deduplicate within this output AND against session history
        out: List[Dict[str, Any]] = []
        local_seen: Set[str] = set()

        for domain, title, why, confidence in candidates:
            signature = _sig(domain, title)
            if signature in local_seen:
                continue
            if signature in self._session_seen:
                logger.debug("RecommendationEngine: skipping duplicate sig=%s", signature)
                continue
            local_seen.add(signature)
            self._session_seen.add(signature)
            out.append({
                "domain": domain,
                "title": title,
                "why": why,
                "confidence": confidence,
                "signature": signature,
            })

        elapsed = time.perf_counter() - t0
        logger.info(
            "RecommendationEngine: generated %d recommendations (%.4fs)",
            len(out), elapsed,
        )
        return out

    def reset_session(self) -> None:
        """Reset session-level duplicate tracking (call at new session start)."""
        self._session_seen.clear()
        logger.debug("RecommendationEngine: session reset")
