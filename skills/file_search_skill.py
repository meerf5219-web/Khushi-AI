"""File search skill for locating files in common user folders."""

from __future__ import annotations

import logging
import os
from typing import List, Optional

logger = logging.getLogger(__name__)

COMMON_FOLDERS = [
    os.path.expanduser("~"),
    os.path.expanduser(r"~\Desktop"),
    os.path.expanduser(r"~\Documents"),
    os.path.expanduser(r"~\Downloads"),
    os.path.expanduser(r"~\Pictures"),
]


class FileSearchSkill:
    """Search for files by name in common folders."""

    def execute(self, text: str) -> Optional[str]:
        """Search for a file whose name appears in the command."""
        logger.info("FileSearchSkill executed with text: %s", text)
        query = self._extract_query(text)
        if not query:
            return None

        matches = self._search_files(query)
        if not matches:
            return f"No files found for {query}."

        return "\n".join(matches[:5])

    def _extract_query(self, text: str) -> Optional[str]:
        """Extract the requested filename from the text."""
        cleaned = text.lower().strip()
        for keyword in ["find", "locate"]:
            if cleaned.startswith(keyword):
                return text.replace(keyword, "", 1).strip() or None
        return None

    def _search_files(self, query: str) -> List[str]:
        """Search common folders for a matching filename."""
        normalized_query = query.lower()
        results: List[str] = []

        for base_dir in COMMON_FOLDERS:
            if not os.path.isdir(base_dir):
                continue

            for root, _, files in os.walk(base_dir):
                for filename in files:
                    if normalized_query in filename.lower():
                        results.append(os.path.join(root, filename))
                        if len(results) >= 10:
                            return results

        return results
