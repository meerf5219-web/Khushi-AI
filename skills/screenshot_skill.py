"""Screenshot skill for capturing the current screen."""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

try:
    import pyautogui
except ImportError:  # pragma: no cover - optional dependency
    pyautogui = None

from utils.resource_manager import RM

logger = logging.getLogger(__name__)


def _screenshot_dir() -> str:
    d = RM.screenshots()
    d.mkdir(parents=True, exist_ok=True)
    return str(d)


class ScreenshotSkill:
    """Capture a screenshot and save it under the screenshots directory."""

    def execute(self, text: str) -> Optional[str]:
        """Capture a screenshot when the command asks for one."""
        logger.info("ScreenshotSkill executed with text: %s", text)
        if not self._is_requested(text):
            return None

        if pyautogui is None:
            return "Screenshot support is unavailable."

        screenshot_dir = _screenshot_dir()
        filename = os.path.join(screenshot_dir, f"screenshot_{int(time.time())}.png")

        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
        except Exception as exc:  # pragma: no cover - runtime dependency
            logger.warning("Screenshot capture failed: %s", exc)
            return "I could not take a screenshot."

        return f"Screenshot saved to {filename}."

    def _is_requested(self, text: str) -> bool:
        """Check whether the input requests a screenshot."""
        normalized_text = text.lower()
        return "screenshot" in normalized_text or "capture screen" in normalized_text or "capture" in normalized_text
