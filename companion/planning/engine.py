from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class PlanningEngine:
    """
    Converts reflection into a simple grounded plan.
    Grounding policy: only echo/structure data from Companion Memory.
    """

    def generate(self, *, summary: Dict[str, Any], reflection: Dict[str, Any]) -> Dict[str, Any]:
        # Keep deterministic structure; no external claims.
        goals = summary.get("goals", {}).get("records", {})
        projects = summary.get("projects", {}).get("records", {})
        habits = summary.get("habits", {}).get("records", {})

        def _values(bucket_records: Any) -> List[str]:
            if isinstance(bucket_records, dict):
                out: List[str] = []
                for rec in bucket_records.values():
                    if isinstance(rec, dict):
                        payload = rec.get("payload", {})
                        if isinstance(payload, dict):
                            out.append(str(payload.get("value") or payload.get("text") or ""))
                return [x for x in out if x]
            return []

        plan_items: List[Dict[str, str]] = []
        g = _values(goals)
        p = _values(projects)
        h = _values(habits)

        if g:
            plan_items.append({"type": "goal-focus", "item": f"Focus on: {g[0]}", "why": "Derived from Companion Memory goals."})
        if p:
            plan_items.append({"type": "project-next-step", "item": f"Next action for: {p[0]}", "why": "Derived from Companion Memory projects."})
        if h:
            plan_items.append({"type": "habit-consistency", "item": f"Maintain habit: {h[0]}", "why": "Derived from Companion Memory habits."})

        # Always include reflection notes (grounded)
        daily_items = reflection.get("daily", {}).get("items", [])
        if daily_items:
            plan_items.append({"type": "reflection", "item": "Review today's stored memory items", "why": "Derived from reflection daily items."})

        return {
            "strategy": "companion-memory-grounded",
            "plan_items": plan_items,
        }
