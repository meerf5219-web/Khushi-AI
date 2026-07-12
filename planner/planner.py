import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Planner:
    """Turn a multi-step user request into an ordered list of executable tasks."""

    def __init__(self) -> None:
        self._step_keywords = {
            "OPEN_APP": ["open", "launch", "start"],
            "SEARCH": ["search", "google"],
            "NOTE_CREATE": ["create a note", "take note", "create note"],
            "NOTE_SHOW": ["show notes", "show note", "list notes"],
            "OPEN_URL": ["go to", "open website", "visit"],
            "TIME": ["time", "clock"],
            "SCREENSHOT": ["screenshot", "take screenshot", "capture screen", "capture"],
        }

    def create_plan(self, text: str) -> List[Dict[str, Any]]:
        """Create a task plan from the given user request."""
        normalized_text = text.strip()
        if not normalized_text:
            return []

        logger.info("Planning: %s", normalized_text)
        clauses = self._split_clauses(normalized_text)
        steps: List[Dict[str, Any]] = []

        for clause in clauses:
            lowered = clause.lower().strip()
            if not lowered:
                continue

            if any(keyword in lowered for keyword in self._step_keywords["OPEN_APP"]):
                app = self._extract_app_name(lowered)
                if app:
                    steps.append({"intent": "OPEN_APP", "entity": app, "text": clause})

            if any(keyword in lowered for keyword in self._step_keywords["OPEN_URL"]):
                url = self._extract_url(lowered)
                if url:
                    steps.append({"intent": "OPEN_URL", "entity": url, "text": clause})

            if any(keyword in lowered for keyword in self._step_keywords["SEARCH"]):
                query = self._extract_search_query(lowered)
                if query:
                    steps.append({"intent": "SEARCH", "entity": query, "text": clause})

            if any(keyword in lowered for keyword in self._step_keywords["NOTE_CREATE"]):
                steps.append({"intent": "NOTE_CREATE", "entity": None, "text": clause})

            if any(keyword in lowered for keyword in self._step_keywords["NOTE_SHOW"]):
                steps.append({"intent": "NOTE_SHOW", "entity": None, "text": clause})

            if any(keyword in lowered for keyword in self._step_keywords["TIME"]):
                steps.append({"intent": "TIME", "entity": None, "text": clause})

            if any(keyword in lowered for keyword in self._step_keywords["SCREENSHOT"]):
                steps.append({"intent": "SCREENSHOT", "entity": None, "text": clause})

        if not steps:
            logger.info("No plan created for: %s", normalized_text)
            return []

        logger.info("Planned %s step(s)", len(steps))
        return steps

    def plan(self, text: str) -> List[Dict[str, Any]]:
        """Backward-compatible wrapper for creating a task plan."""
        return self.create_plan(text)

    def _split_clauses(self, text: str) -> List[str]:
        cleaned = text.replace(",", " ").replace(";", " ")
        parts = re.split(r"\b(?:and|then|after|next|followed by)\b", cleaned, flags=re.IGNORECASE)
        return [part.strip() for part in parts if part and part.strip()]

    def _extract_app_name(self, text: str) -> Optional[str]:
        for app in ["chrome", "notepad", "calculator", "paint"]:
            if app in text:
                return app
        return None

    def _extract_search_query(self, text: str) -> Optional[str]:
        for keyword in ["search", "google"]:
            if keyword in text:
                query = text.replace(keyword, "", 1).strip()
                if query:
                    return query.replace("and", "").strip().title()
        return None

    def _extract_url(self, text: str) -> Optional[str]:
        for keyword in ["go to", "open website", "visit"]:
            if keyword in text:
                url = text.replace(keyword, "", 1).strip()
                return url or None
        return None
