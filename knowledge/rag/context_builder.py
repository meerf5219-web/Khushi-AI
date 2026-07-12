from __future__ import annotations

"""
Phase-5 wrapper-only module.

Current working context assembly lives in `khushi/knowledge/rag_engine.py`.

This module exists for the new architecture layout without migrating
the running pipeline yet.
"""

from typing import Any, Dict, List, Optional, Sequence


class ContextBuilder:
    """Compatibility wrapper to assemble a grounded context string."""

    def build_context(
        self,
        *,
        query: str,  # kept for interface compatibility
        matches: Sequence[Dict[str, Any]],
        top_k: int,
    ) -> List[str]:
        # Keep format consistent with legacy RAGEngine to avoid behavior drift.
        context_blocks: List[str] = []
        for i, m in enumerate(matches[:top_k], start=1):
            chunk_id = (m.get("metadata") or {}).get("chunk_id") or m.get("id") or f"chunk_{i}"
            collection = (m.get("metadata") or {}).get("collection") or ""
            filename = (m.get("metadata") or {}).get("filename") or ""
            page = (m.get("metadata") or {}).get("page") or "N/A"
            chunk_text = m.get("document") or m.get("text") or ""

            context_blocks.append(
                f"[Source {i} | Document={filename} | Collection={collection} | Page={page} | Chunk={chunk_id}]\n{chunk_text}"
            )
        return context_blocks
