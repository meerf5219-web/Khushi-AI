from __future__ import annotations

from typing import Any, Optional

from providers.provider_base import ProviderBase


class DummyProvider(ProviderBase):
    """Placeholder provider until a real AI model is connected."""

    def generate(self, text: str, *, context: Optional[dict[str, Any]] = None) -> str:
        return "I'm not connected to an AI model yet."
