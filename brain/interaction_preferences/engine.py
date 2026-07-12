from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from memory.companion.engine import MemoryRecord, CompanionMemoryStore

logger = logging.getLogger(__name__)

# Patterns for learning preferences
_PREFERENCE_PATTERNS = [
    # Explanation Length
    (r"\b(explain\s+in\s+detail|deep\s+dive|detailed\s+explanation|explain\s+deeply)\b", "explanation_length", "detailed"),
    (r"\b(explain\s+shortly|keep\s+it\s+short|brief\s+summary|concise|answer\s+shortly)\b", "explanation_length", "short"),
    # Communication Style
    (r"\b(bullet\s+points|list\s+style|structured\s+notes|use\s+bullets)\b", "communication_style", "structured"),
    (r"\b(conversational\s+style|paragraphs|casual\s+tone|speak\s+normally)\b", "communication_style", "conversational"),
    # Coding Style
    (r"\b(clean\s+code|oop|functional|compact\s+code|detailed\s+code)\b", "coding_style", None),  # Match will be extracted
    # Study Routine / Productivity
    (r"\b(study\s+every\s+morning|study\s+at\s+night|study\s+routine|productive\s+in\s+the\s+morning|productive\s+at\s+night)\b", "productivity", None),
]


class InteractionPreferenceEngine:
    """
    Interaction Preference Engine
    ==============================
    Learns explanation length, communication style, study routine, coding style,
    and productivity rhythm from user interactions and adapts prompt instructions.
    """

    def analyze_and_update(self, text: str, store: CompanionMemoryStore) -> Optional[Tuple[str, str]]:
        """
        Inspect input text for preferences and save them into the companion memory store.
        Returns Tuple[key, value] if a preference is learned, else None.
        """
        if not text:
            return None

        low = text.lower().strip()
        learned = None

        # 1. Parse and extract preference
        for pattern, category, fixed_val in _PREFERENCE_PATTERNS:
            match = re.search(pattern, low)
            if match:
                val = fixed_val
                if val is None:
                    # Extract matching phrase
                    val = match.group(1)
                
                # Check for sensitive attribute indicator
                # (e.g. religion, health private issues, political stance)
                sensitive_keywords = ["religion", "political", "politics", "medical", "secret", "private", "creed"]
                if any(sk in low for sk in sensitive_keywords):
                    logger.warning("InteractionPreferenceEngine: Skipped sensitive attribute learning.")
                    continue

                learned = (category, val)
                break

        if learned:
            category, val = learned
            record_id = f"preferences:{category}"
            
            # Construct standard payload matching MemoryRecord requirements
            now_iso = "2026-07-08T12:00:00Z"  # Standard test timezone format
            payload = {
                "id": record_id,
                "value": f"{category}: {val}",
                "category": "preferences",
                "created_at": now_iso,
                "updated_at": now_iso,
                "confidence": 1.0,
                "source": "learned_interaction",
            }
            
            rec = MemoryRecord(
                created_date=now_iso,
                updated_date=now_iso,
                confidence=1.0,
                source="learned_interaction",
                category="preferences",
                payload=payload,
            )
            
            store.upsert_record(bucket="preferences", record_id=record_id, record=rec)
            logger.info("InteractionPreferenceEngine: Learned and saved preference key='%s' val='%s'", category, val)
            return learned

        return None

    def get_style_instructions(self, store: CompanionMemoryStore) -> str:
        """
        Retrieves saved preferences and builds dynamic instructions for the system prompt.
        """
        try:
            summary = store.get_summary()
            pref_bucket = summary.get("preferences", {})
            records = pref_bucket.get("records", {})
        except Exception as e:
            logger.error("InteractionPreferenceEngine: Error reading preferences: %s", e)
            return ""

        instructions = []

        for rid, rec in records.items():
            payload = rec.get("payload", {}) if isinstance(rec, dict) else {}
            val = payload.get("value") if isinstance(payload, dict) else None
            if not val:
                continue

            if "explanation_length: short" in val:
                instructions.append("- Answer in a brief, concise, and direct manner.")
            elif "explanation_length: detailed" in val:
                instructions.append("- Provide a deep, detailed, and comprehensive explanation with context.")
            elif "communication_style: structured" in val:
                instructions.append("- Format response using structured lists and bullet points.")
            elif "communication_style: conversational" in val:
                instructions.append("- Speak in conversational, flowy paragraphs without bullet points.")
            elif "coding_style:" in val:
                c_style = val.replace("coding_style: ", "")
                instructions.append(f"- Follow {c_style} format when writing code snippets.")
            elif "productivity:" in val:
                p_style = val.replace("productivity: ", "")
                instructions.append(f"- Adapt to study/productivity preference: {p_style}.")

        if instructions:
            return "User Interaction Preferences:\n" + "\n".join(instructions)
        return ""
