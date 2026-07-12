from __future__ import annotations

"""
Module 6: Multi-Intent Parser
===============================
Splits combined commands into individual sub-queries.

Examples:
  "Open Chrome and tell me the weather."
    → ["Open Chrome", "tell me the weather"]

  "Remember my goal and show my timeline."
    → ["Remember my goal", "show my timeline"]

  "Search Python and open Chrome."
    → ["Search Python", "open Chrome"]

Strategy:
- Conjunction-based splitting (and, then, also, plus, after that)
- Preserves context / order
- Only splits when both halves contain identifiable intent signals
- Returns original text as single-item list if no valid split found
"""

import logging
import re
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Conjunctions that may indicate multi-intent
_CONJUNCTIONS = [
    r"\band\s+then\b",
    r"\band\s+also\b",
    r"\band\b",
    r"\bthen\b",
    r"\bafter\s+that\b",
    r"\balso\b",
    r"\bplus\b",
]

# Intent signal keywords (any of these in a sub-query → likely has an intent)
_INTENT_SIGNALS = [
    "open", "launch", "start", "close",
    "search", "find", "look up", "google",
    "remember", "recall", "show", "tell", "display",
    "calculate", "compute",
    "take screenshot", "screenshot",
    "what", "who", "where", "when", "why", "how",
    "time", "date", "weather",
    "note", "notes",
    "play", "stop", "volume", "brightness",
    "reflect", "recommend", "profile", "timeline",
    "goal", "habit", "project",
]

_SPLIT_PATTERN = re.compile(
    r"\s*(?:" + "|".join(_CONJUNCTIONS) + r")\s*",
    re.IGNORECASE,
)

# Minimum length for a valid sub-query (avoid "and" splitting "rock and roll")
_MIN_SUBQUERY_LEN = 4


def _has_intent_signal(text: str) -> bool:
    """Return True if text contains at least one intent signal word."""
    lower = text.lower()
    return any(signal in lower for signal in _INTENT_SIGNALS)


def _is_valid_split(parts: List[str]) -> bool:
    """Check that all parts look like independent queries."""
    if len(parts) < 2:
        return False
    valid = [p.strip() for p in parts if len(p.strip()) >= _MIN_SUBQUERY_LEN]
    if len(valid) < 2:
        return False
    # Each part must have at least one intent signal
    return all(_has_intent_signal(p) for p in valid)


class MultiIntentParser:
    """
    Detects and splits multi-intent queries into sub-queries.

    Policy:
    - Only splits if both halves look like independent commands.
    - Returns the original text as a single-item list if not a multi-intent query.
    - Preserves order of commands.
    """

    def parse(self, text: str) -> Tuple[bool, List[str]]:
        """
        Parse text for multiple intents.

        Returns:
            (is_multi_intent, list_of_sub_queries)
        """
        if not text or len(text.strip()) < 10:
            return False, [text]

        parts = _SPLIT_PATTERN.split(text)
        parts = [p.strip() for p in parts if p.strip()]

        if _is_valid_split(parts):
            logger.info("MultiIntentParser: split '%s' → %s", text, parts)
            return True, parts

        # Try a stricter split on ", and " pattern
        comma_and_parts = re.split(r",\s*and\s+", text, flags=re.IGNORECASE)
        if len(comma_and_parts) >= 2 and _is_valid_split(comma_and_parts):
            logger.info("MultiIntentParser: comma-and split '%s' → %s", text, comma_and_parts)
            return True, comma_and_parts

        return False, [text]
