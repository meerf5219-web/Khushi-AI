from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Indirect intent mappings (regex patterns to canonical queries)
_INDIRECT_INTENT_PATTERNS = [
    # Weather indirects
    (r"\b(do\s+i\s+need\s+an\s+umbrella|is\s+it\s+raining|is\s+it\s+cold|is\s+it\s+hot|what\s+is\s+the\s+climate|temperature)\b", "weather"),
    # App open indirects
    (r"\b(can\s+you\s+open|would\s+you\s+mind\s+opening|launch|start|open)\s+([a-zA-Z0-9\s]+)\b", r"open \2"),
    # Reminder indirects
    (r"\b(can\s+you\s+remind\s+me|make\s+a\s+reminder|remind\s+me\s+later|set\s+a\s+reminder)\b", "set a reminder"),
    # Calculation indirects
    (r"\b(calculate|what\s+is)\s+(\d+\s*[\+\-\*\/]\s*\d+)\b", r"calculate \2"),
]

# Acknowledgement patterns
_ACK_PATTERNS = [
    r"\b(thank\s+you|thanks|thx|tks)\b",
    r"\b(ok|okay|cool|great|awesome|perfect|that\s+is\s+it)\b",
]

# Repair patterns
_REPAIR_PATTERNS = [
    r"^(no|cancel|cancel\s+that|incorrect|not\s+that|wrong)\s*,?\s*(open\s+)?([a-zA-Z0-9\s]+)$",
]


class NaturalConversationEngine:
    """
    Tracks state across multiple turns.
    Resolves ellipsis, pronouns, indirect intents, and handles acknowledgements and repairs.
    """

    def __init__(self) -> None:
        self.state: Dict[str, Any] = {
            "last_intent": None,
            "last_location": None,
            "last_app": None,
            "last_time": None,
            "last_query": None,
        }

    def process_turn(
        self, text: str, recent_turns: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Process the current user turn.
        Returns:
            Tuple[rewritten_query, direct_response]
            If direct_response is not None, the system should immediately return it.
        """
        if not text or not text.strip():
            return "", None

        normalized = text.lower().strip().rstrip("?.!,")
        logger.info("NaturalConversationEngine: Processing query='%s'", normalized)

        # 1. Natural Acknowledgement check
        for pattern in _ACK_PATTERNS:
            if re.search(pattern, normalized):
                logger.info("NaturalConversationEngine: Detected acknowledgement.")
                if "thank" in normalized:
                    return text, "You're welcome Faisal. Happy to help."
                return text, "Understood Faisal. Let me know if you need anything else."

        # 2. Conversation Repair check (e.g. "No, calculator")
        for pattern in _REPAIR_PATTERNS:
            match = re.match(pattern, normalized)
            if match:
                corrected_subject = match.group(3).strip()
                logger.info("NaturalConversationEngine: Detected repair. Corrected target='%s'", corrected_subject)
                # Map to open application
                for app in ["chrome", "notepad", "calculator", "paint"]:
                    if app in corrected_subject:
                        self.state["last_intent"] = "OPEN_APP"
                        self.state["last_app"] = app
                        return f"open {app}", None
                return f"{corrected_subject}", None

        # 3. Indirect Intent Recognition
        query = normalized
        for pattern, replacement in _INDIRECT_INTENT_PATTERNS:
            if re.search(pattern, normalized):
                query = re.sub(pattern, replacement, normalized).strip()
                logger.info("NaturalConversationEngine: Mapped indirect intent. Rewritten='%s'", query)
                break

        # 4. Ellipsis and Pronoun Resolution
        resolved_query = self._resolve_ellipsis_and_pronouns(query)
        if resolved_query != query:
            logger.info("NaturalConversationEngine: Resolved ellipsis/pronouns. Final='%s'", resolved_query)
            query = resolved_query

        # 5. Extract state variables for context tracking
        self._update_state_variables(query)

        return query, None

    def _resolve_ellipsis_and_pronouns(self, text: str) -> str:
        """
        Resolves ellipsis like "how about tomorrow?" or "in Mumbai?".
        """
        # Ellipsis Case 1: "how about [time]?" / "what about [time]?" / "tomorrow?"
        time_match = re.search(
            r"\b(how\s+about|what\s+about)?\s*(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
            text,
        )
        if time_match:
            time_val = time_match.group(2)
            if self.state["last_intent"] == "WEATHER":
                loc = self.state["last_location"] or "delhi"
                return f"weather in {loc} {time_val}"

        # Ellipsis Case 2: "how about [location]?" / "in [location]?"
        # Standard list of cities for testing
        cities = ["mumbai", "delhi", "kashmir", "london", "new york", "paris"]
        for city in cities:
            if city in text:
                if self.state["last_intent"] == "WEATHER":
                    t_val = self.state["last_time"] or "today"
                    return f"weather in {city} {t_val}"

        # Pronoun Case: "open it" -> open last app
        if re.search(r"\b(open\s+it|launch\s+it|start\s+it)\b", text):
            if self.state["last_app"]:
                return f"open {self.state['last_app']}"

        return text

    def _update_state_variables(self, query: str) -> None:
        """
        Updates multi-turn state variables based on the active query.
        """
        # Determine intent category
        if "weather" in query:
            self.state["last_intent"] = "WEATHER"
            # Extract location
            cities = ["mumbai", "delhi", "kashmir", "london", "new york", "paris"]
            for city in cities:
                if city in query:
                    self.state["last_location"] = city
            # Extract time
            times = ["today", "tomorrow", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            for t in times:
                if t in query:
                    self.state["last_time"] = t
        elif "open" in query or "launch" in query:
            self.state["last_intent"] = "OPEN_APP"
            for app in ["chrome", "notepad", "calculator", "paint"]:
                if app in query:
                    self.state["last_app"] = app
        elif "remind" in query or "reminder" in query:
            self.state["last_intent"] = "REMINDER"
        
        self.state["last_query"] = query
        logger.debug("NaturalConversationEngine: State updated to: %s", self.state)
