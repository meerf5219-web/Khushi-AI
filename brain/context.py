"""Conversation context manager for resolving ambiguous references."""

from __future__ import annotations

import logging
import re
from typing import Dict, Optional

logger = logging.getLogger(__name__)
PRONOUN_PATTERN = re.compile(r"\b(he|she|it|they|that|this|there|those)\b", re.IGNORECASE)


class ContextManager:
    """Track recent conversation context and rewrite ambiguous references."""

    def __init__(self) -> None:
        self.last_person: Optional[str] = None
        self.last_topic: Optional[str] = None
        self.last_app: Optional[str] = None
        self.last_search: Optional[str] = None
        self.last_response: Optional[str] = None

    def rewrite(self, text: str) -> str:
        """Rewrite ambiguous text using stored context when possible."""
        original_text = text.strip()
        normalized_text = original_text.lower()

        if not normalized_text:
            return original_text

        replacement = self._resolve_reference(normalized_text)
        if replacement is None:
            logger.info("No context rewrite applied to: %s", original_text)
            return original_text

        rewritten_text = self._replace_pronouns(original_text, replacement)
        logger.info("Original sentence: %s", original_text)
        logger.info("Rewritten sentence: %s", rewritten_text)
        return rewritten_text

    def update(self, text: str, response: str) -> None:
        """Update the stored context based on a user utterance and assistant response."""
        lowered = text.lower().strip()
        if not lowered:
            return

        if "who is" in lowered:
            entity = self._strip_keyword(text, "who is")
            self.last_person = entity or self.last_person
            self.last_topic = entity or self.last_topic

        if "what is" in lowered or "how old" in lowered:
            self.last_topic = self.last_topic or self.last_person

        if "open" in lowered or "launch" in lowered or "start" in lowered:
            self.last_app = self._extract_app_name(lowered)

        if "search" in lowered or "google" in lowered:
            self.last_search = self._extract_search_query(lowered)

        self.last_response = response

    def _resolve_reference(self, text: str) -> Optional[str]:
        """Resolve common pronouns to the most recently known context."""
        if PRONOUN_PATTERN.search(text):
            if self.last_person:
                return self.last_person
            if self.last_topic:
                return self.last_topic
            if self.last_app:
                return self.last_app
            if self.last_search:
                return self.last_search
        return None

    def _replace_pronouns(self, text: str, replacement: str) -> str:
        """Replace a pronoun with the resolved context in a sentence."""
        rewritten = PRONOUN_PATTERN.sub(replacement, text, count=1)
        return rewritten.replace("??", "?").replace("!!", "!")

    def _strip_keyword(self, text: str, keyword: str) -> str:
        """Remove a leading keyword from a sentence regardless of casing."""
        pattern = re.compile(rf"^{re.escape(keyword)}\s+", re.IGNORECASE)
        return pattern.sub("", text).strip()

    def _extract_app_name(self, text: str) -> Optional[str]:
        """Extract an application name from the input text."""
        for app in ["chrome", "notepad", "calculator", "paint"]:
            if app in text:
                return app
        return None

    def _extract_search_query(self, text: str) -> Optional[str]:
        """Extract a search query from the input text."""
        for keyword in ["search", "google"]:
            if keyword in text:
                query = text.replace(keyword, "", 1).strip()
                return query or None
        return None
