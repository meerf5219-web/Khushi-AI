"""Weather skill with a provider abstraction for future API integrations."""

from __future__ import annotations

import logging
from typing import Optional, Protocol

logger = logging.getLogger(__name__)


class WeatherProvider(Protocol):
    """Protocol for weather providers."""

    def get_weather(self, location: str) -> str:
        """Return a weather response string for a location."""


class WeatherSkill:
    """Provide weather information through an injectable provider."""

    def __init__(self, provider: Optional[WeatherProvider] = None) -> None:
        self.provider = provider

    def execute(self, text: str) -> Optional[str]:
        """Return weather information for the requested location."""
        logger.info("WeatherSkill executed with text: %s", text)
        location = self._extract_location(text)
        if not location:
            return None

        if self.provider is None:
            return "Weather service is not configured."

        try:
            return self.provider.get_weather(location)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Weather provider failed: %s", exc)
            return "Weather service is not configured."

    def _extract_location(self, text: str) -> Optional[str]:
        """Extract a location from the input text."""
        cleaned = text.strip().lower()
        if not cleaned:
            return None

        for keyword in ["weather", "temperature", "forecast"]:
            if keyword in cleaned:
                query = cleaned.replace(keyword, "", 1).strip()
                return query or None
        return None
