"""Brightness skill for adjusting display brightness when supported."""

from __future__ import annotations

import logging
from typing import Optional

try:
    import screen_brightness_control as sbc
except ImportError:  # pragma: no cover - optional dependency
    sbc = None

logger = logging.getLogger(__name__)


class BrightnessSkill:
    """Adjust display brightness when the platform exposes brightness controls."""

    def execute(self, text: str) -> Optional[str]:
        """Increase, decrease, or report the current brightness."""
        logger.info("BrightnessSkill executed with text: %s", text)
        if sbc is None:
            return "Brightness control is unavailable."

        action = text.lower().strip()
        if action == "current":
            try:
                return f"Current brightness is {sbc.get_brightness()}%."
            except Exception as exc:  # pragma: no cover - optional dependency
                logger.warning("Unable to read brightness: %s", exc)
                return "Brightness control is unavailable."

        if action == "decrease":
            try:
                sbc.set_brightness(max(0, sbc.get_brightness() - 10))
                return "Brightness decreased."
            except Exception as exc:  # pragma: no cover - optional dependency
                logger.warning("Unable to change brightness: %s", exc)
                return "Brightness control is unavailable."

        if action == "increase":
            try:
                sbc.set_brightness(min(100, sbc.get_brightness() + 10))
                return "Brightness increased."
            except Exception as exc:  # pragma: no cover - optional dependency
                logger.warning("Unable to change brightness: %s", exc)
                return "Brightness control is unavailable."

        return None
