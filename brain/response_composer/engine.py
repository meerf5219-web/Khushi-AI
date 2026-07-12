from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from companion.personality.engine import PersonalityEngine

logger = logging.getLogger(__name__)


class ResponseComposer:
    """
    Acts as the final coordinator for all assistant outputs.
    Ensures: Truthfulness (no hallucinations), Conciseness, Readability, Empathy, and Personality.
    """

    def __init__(self) -> None:
        self.personality = PersonalityEngine()

    def compose(
        self,
        raw_text: str,
        emotional_state: Optional[Any] = None,
        style_instructions: str = "",
        profile_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Compose, check, and sanitize raw assistant text before it is spoken/returned.
        """
        if not raw_text or not raw_text.strip():
            return ""

        logger.info("ResponseComposer: Composing final response. Raw length=%d", len(raw_text))

        # 1. Hallucination / Grounding truthfulness check
        grounded_text = self._verify_truthfulness(raw_text, profile_data)

        # 2. Apply dynamic empathy based on emotional state
        empathetic_text = self._add_empathy(grounded_text, emotional_state)

        # 3. Apply personality filters (emotions, consciousness, arrogance)
        sanitized_text = self.personality.filter_response(empathetic_text)

        # 4. Shorten if preference or length requires it
        final_text = self._adjust_formatting_and_length(sanitized_text, style_instructions)

        return final_text

    def _verify_truthfulness(self, text: str, profile_data: Optional[Dict[str, Any]]) -> str:
        """
        Ensure the assistant does not claim memories or facts not actually in Companion Memory.
        """
        profile = profile_data or {}
        
        # Flatten memory values for quick lookup
        memory_words = set()
        for bucket, records in profile.items():
            if isinstance(records, dict):
                for rec in records.values():
                    val = rec.get("payload", {}).get("value") or ""
                    for word in val.lower().split():
                        memory_words.add(word.strip("?,.!:;()\"'"))

        # Look for memory claiming statements like "I remember that you..." or "You told me you..."
        sentences = re.split(r"(?<=[.!?])\s+", text)
        verified_sentences = []

        for sentence in sentences:
            low = sentence.lower()
            if any(marker in low for marker in ["i remember you", "you told me", "your saved", "remember that you"]):
                # Extract nouns/proper nouns or key values and check overlap with memory
                # If the sentence names a specific noun/proper noun (like "paris" or "java") not in memory, we omit/sanitize
                # We do a basic keyword checking for verification
                claim_words = [w.strip("?,.!:;()\"'") for w in low.split() if len(w) > 4]
                # Check if there is any overlap at all. If no overlap with any memory words, we sanitize the sentence
                if claim_words and not any(cw in memory_words for cw in claim_words):
                    logger.warning("ResponseComposer: Hallucination detected and removed: '%s'", sentence)
                    # Rewrite to a general grounding sentence or omit
                    continue
            verified_sentences.append(sentence)

        if not verified_sentences:
            return "I am programmed to assist with your objectives based on stored guidelines."
        return " ".join(verified_sentences)

    def _add_empathy(self, text: str, state: Optional[Any]) -> str:
        """
        Prepend structured, supportive tone updates based on emotional state.
        """
        if state is None or not hasattr(state, "primary_emotion"):
            return text

        empathy_prefix = ""
        # Check emotional dimensions
        if state.primary_emotion == "sadness" and state.intensity > 0.4:
            empathy_prefix = "I acknowledge this outcome can be difficult. Let's look at the facts and determine adjustments. "
        elif state.stress > 0.5:
            empathy_prefix = "I note the high demand of this task. Let's break it down into manageable components. "
        elif state.frustration > 0.5:
            empathy_prefix = "I am here to resolve this problem. Let's isolate the root cause together. "
        elif state.burnout > 0.5:
            empathy_prefix = "Pacing is critical for long-term productivity. Let's evaluate a rest period. "

        if empathy_prefix and empathy_prefix.lower() not in text.lower():
            return empathy_prefix + text
        return text

    def _adjust_formatting_and_length(self, text: str, style_instructions: str) -> str:
        """
        Shortens response or formats it based on preference style instructions.
        """
        low_style = style_instructions.lower()
        
        # Check length shortening
        if "short" in low_style or "concise" in low_style:
            # Shorten to first 2-3 sentences
            sentences = re.split(r"(?<=[.!?])\s+", text)
            if len(sentences) > 3:
                text = " ".join(sentences[:3])
                logger.info("ResponseComposer: Shortened response to: %s", text)

        # Check list layout structuring
        if "structured list" in low_style or "bullet points" in low_style:
            # If response has multiple sentences and no bullets yet, structure it
            if len(text) > 40 and "•" not in text and ("." in text or "," in text):
                # split by sentences
                parts = re.split(r"(?<=[.!?])\s+", text)
                formatted = []
                for p in parts:
                    if p.strip():
                        # strip trailing period to avoid double periods
                        cleaned_p = p.strip().rstrip(".")
                        formatted.append(f"• {cleaned_p.capitalize()}.")
                text = "\n".join(formatted)

        return text
