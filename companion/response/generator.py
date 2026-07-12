from __future__ import annotations

"""
Response Generator
==================
Produces a grounded, structured response from Companion Intelligence outputs.

Policy:
- Uses ONLY: personality + reflection + recommendations + planning.
- All inputs are derived from Companion Memory (no external sources).
- If data is missing, returns a safe "insufficient data" message.
- Response is professional, calm, non-emotional.
- Labels data as Known / Unknown / Estimated where relevant.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ResponseGenerator:
    """
    Response generator for Companion Intelligence.

    Grounding policy:
    - Must only use: personality + reflection + recommendations + planning,
      all of which are derived from Companion Memory (no external calls).
    - If data is missing, respond with a safe "insufficient data" message.
    """

    def generate(
        self,
        *,
        personality: Dict[str, Any],
        reflection: Dict[str, Any],
        recommendations: List[Dict[str, Any]],
        planning: Dict[str, Any],
        continuity_hint: Optional[str] = None,
    ) -> str:
        t0 = time.perf_counter()

        # Determine data availability
        any_reflection_items = any(
            isinstance(reflection.get(freq, {}).get("items"), list)
            and reflection[freq]["items"]
            for freq in ["daily", "weekly", "monthly"]
        )
        any_reco = bool(recommendations)
        any_plan = bool(planning.get("plan_items"))
        any_continuity = bool(continuity_hint)

        if not any_reflection_items and not any_reco and not any_plan and not any_continuity:
            elapsed = time.perf_counter() - t0
            logger.info("ResponseGenerator: insufficient data (%.4fs)", elapsed)
            return (
                "Companion Intelligence: I couldn't find enough stored information in your "
                "Companion Memory to generate a reflection or recommendations yet. "
                "Try: 'Remember that my goal is to crack UPSC' to get started."
            )

        lines: List[str] = []
        lines.append("Companion Intelligence Summary")
        lines.append("=" * 40)

        # Personality style line
        style = personality.get("style") or "Professional, calm, supportive"
        lines.append(f"Tone: {style}")
        lines.append("")

        # Continuity hint (if applicable)
        if any_continuity and continuity_hint:
            lines.append(f"[Context] {continuity_hint}")
            lines.append("")

        # Reflection sections
        for freq in ["daily", "weekly", "monthly"]:
            block = reflection.get(freq, {})
            items = block.get("items", [])
            natural = block.get("natural_summary", "")
            note = block.get("note", "")

            lines.append(f"--- {freq.upper()} REFLECTION ---")
            if natural:
                lines.append(f"[Known] {natural}")
            else:
                lines.append(f"[Unknown] No {freq} items found in Companion Memory.")
            if items:
                for it in items[:6]:
                    val = it.get("value") or ""
                    cat = it.get("category") or ""
                    conf = it.get("confidence")
                    label = "Known" if conf and float(conf) >= 0.8 else "Estimated"
                    if val:
                        lines.append(f"  [{label}] [{cat}] {val}")
            if note:
                lines.append(f"  Note: {note}")
            lines.append("")

        # Recommendations section
        lines.append("--- RECOMMENDATIONS ---")
        if recommendations:
            for r in recommendations[:6]:
                domain = r.get("domain", "")
                title = r.get("title", "")
                why = r.get("why", "")
                conf = r.get("confidence", 0.0)
                conf_pct = int(float(conf) * 100)
                lines.append(f"[{domain}] {title}")
                lines.append(f"  Why: {why}")
                lines.append(f"  Confidence: {conf_pct}%")
                lines.append("")
        else:
            lines.append("[Unknown] No grounded recommendations available yet.")
            lines.append("")

        # Planning section
        lines.append("--- NEXT ACTIONS (Grounded Plan) ---")
        plan_items = planning.get("plan_items") or []
        if plan_items:
            for p in plan_items[:5]:
                item = p.get("item", "")
                why = p.get("why", "")
                lines.append(f"• {item}")
                if why:
                    lines.append(f"  ({why})")
        else:
            lines.append("• Review your stored goals, habits, and projects.")
        lines.append("")

        # Epistemic footer
        lines.append(
            "Note: All information above is sourced from your Companion Memory. "
            "Nothing has been invented or inferred beyond what you have stored."
        )

        result = "\n".join(lines)

        elapsed = time.perf_counter() - t0
        logger.info("ResponseGenerator: generated response length=%d (%.4fs)", len(result), elapsed)
        return result
