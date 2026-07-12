"""Clipboard skill for copying, pasting, and showing clipboard content."""

from __future__ import annotations

import logging
from typing import Optional

try:
    import pyperclip
except ImportError:  # pragma: no cover - optional dependency
    pyperclip = None

logger = logging.getLogger(__name__)


class ClipboardSkill:
    """Access the system clipboard."""

    def execute(self, text: str) -> Optional[str]:
        """Perform the requested clipboard action."""
        logger.info("ClipboardSkill executed with text: %s", text)
        if pyperclip is None:
            return "Clipboard support is unavailable."

        action = text.lower().strip()
        if action == "copy":
            return "Clipboard copy is not configured."
        if action == "paste":
            try:
                return pyperclip.paste()
            except Exception as exc:  # pragma: no cover - environment dependent
                logger.warning("Clipboard paste failed: %s", exc)
                return "Clipboard support is unavailable."
        if action == "show":
            return "Clipboard support is unavailable."
        return None
