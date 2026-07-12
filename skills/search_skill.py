import logging
import webbrowser
from typing import Optional

logger = logging.getLogger(__name__)


class SearchSkill:
    """Launch a Google search request in the default web browser."""

    def execute(self, text: str) -> Optional[str]:
        """Open a web search for the provided query if requested."""
        normalized_text = text.lower()

        if "search" not in normalized_text:
            return None

        query = normalized_text.replace("search", "", 1).strip()
        if not query:
            return "What would you like me to search for?"

        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        try:
            webbrowser.open(url)
        except webbrowser.Error as exc:
            logger.warning("Unable to open browser for search: %s", exc)

        return f"Searching for {query}."