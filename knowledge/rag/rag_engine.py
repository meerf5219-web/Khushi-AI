from __future__ import annotations

"""
Phase-5 wrapper-only module.

Current working pipeline lives in `khushi/knowledge/rag_engine.py`.
This module provides the new layout entrypoint without migrating
the running pipeline yet.
"""

from typing import Any, Dict, List, Optional, Tuple

from knowledge.rag_engine import RAGEngine as LegacyRAGEngine


class RAGEngine:
    """Compatibility wrapper delegating to the legacy RAGEngine."""

    def __init__(self, *, provider: Optional[Any] = None) -> None:
        self._legacy = LegacyRAGEngine(provider=provider)  # type: ignore[arg-type]

    def generate_answer(
        self,
        *,
        query: str,
        matches: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        return self._legacy.generate_answer(query=query, matches=matches, metadata=metadata)
