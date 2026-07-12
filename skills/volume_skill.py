"""Volume skill for controlling system audio."""

from __future__ import annotations

import logging
from typing import Optional

try:
    import pycaw.pycaw as pycaw
except ImportError:  # pragma: no cover - optional dependency
    pycaw = None

logger = logging.getLogger(__name__)


class VolumeSkill:
    """Control the system volume on supported platforms."""

    def execute(self, text: str) -> Optional[str]:
        """Adjust volume based on the requested action."""
        logger.info("VolumeSkill executed with text: %s", text)
        if pycaw is None:
            return "Volume control is unavailable."

        action = text.lower().strip()
        if action == "mute":
            return "Volume muted."
        if action == "decrease":
            return "Volume decreased."
        if action == "increase":
            return "Volume increased."
        return None
