from __future__ import annotations

"""
Conflict Resolver
==================
Detects when new information conflicts with stored Companion Memory.
Asks before replacing. Maintains revision history.
Never invents context.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def _normalize(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


@dataclass
class ConflictResult:
    """Result of a conflict check."""
    conflict_detected: bool
    bucket: str
    old_value: Optional[str]
    new_value: str
    record_id: Optional[str]
    # If conflict_detected is True, a confirmation message is set.
    confirmation_message: Optional[str]


class ConflictResolver:
    """
    Checks incoming values against Companion Memory for conflicts.

    Policy:
    - A conflict is detected when a DIFFERENT value exists for the same
      semantic key (same bucket + same record_id).
    - Never silently overwrite — returns confirmation_message for the caller
      to present to the user.
    - Maintains revision_history metadata (caller is responsible for storage).
    """

    def check(
        self,
        *,
        summary: Dict[str, Any],
        bucket: str,
        new_value: str,
        record_id: Optional[str] = None,
    ) -> ConflictResult:
        """
        Check if new_value conflicts with any existing record in bucket.

        Returns ConflictResult with conflict_detected=True and a
        confirmation_message if a conflict is found.
        """
        t0 = time.perf_counter()

        norm_new = _normalize(new_value)
        if not norm_new:
            elapsed = time.perf_counter() - t0
            logger.debug("ConflictResolver.check: empty value, no conflict (%.4fs)", elapsed)
            return ConflictResult(
                conflict_detected=False,
                bucket=bucket,
                old_value=None,
                new_value=new_value,
                record_id=None,
                confirmation_message=None,
            )

        bucket_data = summary.get(bucket, {})
        records = bucket_data.get("records", {}) if isinstance(bucket_data, dict) else {}
        if not isinstance(records, dict):
            elapsed = time.perf_counter() - t0
            logger.debug("ConflictResolver.check: bucket %s has no dict records (%.4fs)", bucket, elapsed)
            return ConflictResult(
                conflict_detected=False,
                bucket=bucket,
                old_value=None,
                new_value=new_value,
                record_id=None,
                confirmation_message=None,
            )

        conflicts: List[Tuple[str, str]] = []

        for rid, rec in records.items():
            if not isinstance(rec, dict):
                continue
            payload = rec.get("payload", {}) if isinstance(rec, dict) else {}
            if not isinstance(payload, dict):
                continue
            # Skip deleted records
            if payload.get("status") == "deleted":
                continue
            old_val = payload.get("value") or payload.get("text") or ""
            norm_old = _normalize(str(old_val))

            # Conflict: same bucket, different value, for same record_id (or any if record_id not specified)
            if norm_old and norm_old != norm_new:
                if record_id is None or rid == record_id:
                    conflicts.append((rid, str(old_val)))

        elapsed = time.perf_counter() - t0

        if conflicts:
            old_rid, old_val = conflicts[0]
            msg = (
                f"I already have '{old_val}' stored under '{bucket}'. "
                f"You're asking me to remember '{new_value}' instead. "
                f"Would you like me to replace it? (yes/no)"
            )
            logger.info(
                "ConflictResolver: conflict detected bucket=%s old='%s' new='%s' (%.4fs)",
                bucket, old_val, new_value, elapsed,
            )
            return ConflictResult(
                conflict_detected=True,
                bucket=bucket,
                old_value=old_val,
                new_value=new_value,
                record_id=old_rid,
                confirmation_message=msg,
            )

        logger.debug("ConflictResolver.check: no conflict (%.4fs)", elapsed)
        return ConflictResult(
            conflict_detected=False,
            bucket=bucket,
            old_value=None,
            new_value=new_value,
            record_id=None,
            confirmation_message=None,
        )

    def build_revision_entry(
        self,
        *,
        old_value: str,
        old_confidence: float,
        old_updated_at: Optional[str],
        old_revision: int,
    ) -> Dict[str, Any]:
        """Build a revision history entry for a conflicting record being replaced."""
        return {
            "revision": old_revision,
            "value": old_value,
            "updated_at": old_updated_at,
            "confidence": old_confidence,
        }
