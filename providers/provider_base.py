from __future__ import annotations

from typing import Any, Optional


class ProviderBase:
    """Base class/interface for AI providers."""

    def generate(self, text: str, *, context: Optional[dict[str, Any]] = None) -> str:
        """Generate a response from the provider."""
        raise NotImplementedError
