from __future__ import annotations

"""
Phase-5 wrapper-only module.

The current working prompt construction and grounded-answer behavior
lives inside `khushi/knowledge/rag_engine.py`.

This module exists only to provide the new layout without migrating
the running pipeline yet.
"""

from typing import Any, Dict


class PromptBuilder:
    """Compatibility wrapper around the legacy RAG prompt building."""

    def build_prompt(self, *, query: str, context: str, metadata: Dict[str, Any]) -> str:
        # Mirror the legacy prompt format to keep behavior consistent.
        return (
            "You are Khushi AI. Answer the user's question using ONLY the provided sources.\n"
            "Rules:\n"
            "- If the sources do not contain the answer, say you couldn't find it.\n"
            "- Keep the answer concise and helpful.\n"
            "- Do not invent document titles, pages, or quotes.\n\n"
            f"User question:\n{query}\n\n"
            f"Sources:\n{context}\n"
        )
