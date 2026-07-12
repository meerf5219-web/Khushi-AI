from __future__ import annotations

"""
Phase-5 wrapper-only module.

Current working response generation and source attribution
lives inside `khushi/knowledge/rag_engine.py`.

This module exists only to provide the new layout without migrating
the running pipeline yet.
"""

from typing import Any, Dict, List, Optional, Protocol


class ResponseGenerator(Protocol):
    def generate(
        self,
        *,
        prompt: str,
        context: Dict[str, Any],
    ) -> str: ...


class DefaultResponseGenerator:
    """Compatibility generator that delegates to legacy RAGEngine."""

    def __init__(self) -> None:
        # Late import to avoid circular deps during test discovery.
        from knowledge.rag_engine import RAGEngine

        self._engine = RAGEngine()

    def generate_answer(self, *, query: str, matches: List[Dict[str, Any]]) -> str:
        answer, _trace = self._engine.generate_answer(query=query, matches=matches)
        return answer
