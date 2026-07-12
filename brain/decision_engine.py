from __future__ import annotations

import logging
from typing import Any, Dict, List, Literal, Optional

from providers.ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)

Decision = Literal["SKILL", "AI"]


class DecisionEngine:
    """
    Hybrid decision engine:
    - Returns "SKILL" when the intent belongs to implemented skills.
    - Returns "AI" when the intent should be handled by an LLM provider.
    """

    def __init__(self, *, implemented_skill_intents: Optional[set[str]] = None) -> None:
        self._implemented_skill_intents: set[str] = implemented_skill_intents or {
            # Must at least cover CALCULATE and WEATHER (requirement notes).
            "OPEN_APP",
            "OPEN_URL",
            "SEARCH",
            "WEB_SEARCH",
            "KNOWLEDGE_QUERY",
            "CALCULATE",
            "WEATHER",
            "NOTE_CREATE",
            "NOTE_SHOW",
            "NOTE_DELETE",
            "SCREENSHOT",
            "SYSTEM",
            "CLIPBOARD",
            "VOLUME",
            "BRIGHTNESS",
            "FILE_SEARCH",
            "FILE",
            "TIME",
            "DATE",
            # Memory-related intents are also routed by Router today.
            "REMEMBER",
            "SAVE_MEMORY",
            "RECALL_MEMORY",
            "NAME",
            "LIFE_MEMORY",
            "GREETING",
            "GOODBYE",
        }

        # AI provider (pluggable). Brain does not need to know any implementation details.
        self._ai_provider = OllamaProvider()

    def decide(self, intent: str, plan: List[Dict[str, Any]]) -> Decision:
        """
        Decide whether this request should be handled by an executable SKILL or by an AI provider.

        Args:
            intent: Detected intent name.
            plan: Planned steps (currently unused for decision, but accepted for future extensions).

        Returns:
            "SKILL" or "AI"
        """
        _ = plan  # reserved for future decision strategies

        # Known "general knowledge" intent must go to LLM.
        if intent == "GENERAL_QUERY":
            logger.info("Decision: LLM")
            return "AI"

        decision: Decision = "SKILL" if intent in self._implemented_skill_intents else "AI"
        logger.info("Decision: %s", "SKILL" if decision == "SKILL" else "AI")
        return decision

    def generate_ai(self, text: str, *, context: Optional[dict[str, Any]] = None) -> str:
        """Generate response using the currently configured AI provider."""
        return self._ai_provider.generate(text, context=context)
