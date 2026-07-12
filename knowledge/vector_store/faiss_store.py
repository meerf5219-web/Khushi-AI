from __future__ import annotations

"""
Compatibility wrapper for FAISS-backed vector store.

FAISS is intentionally NOT required for this project right now.
This is a stub implementation that preserves the interface.
"""

from typing import Any, Dict, List, Optional, Sequence

from knowledge.vector_store.base import VectorStore


class FaissVectorStore(VectorStore):
    """Stub FAISS vector store (returns empty results)."""

    def __init__(self) -> None:
        # No-op: FAISS not required.
        self._collections: Dict[str, List[Dict[str, Any]]] = {}

    def upsert(
        self,
        *,
        collection: str,
        ids: Sequence[str],
        embeddings: Sequence[List[float]],
        documents: Sequence[str],
        metadatas: Sequence[Dict[str, Any]],
    ) -> None:
        items: List[Dict[str, Any]] = self._collections.get(collection, [])
        for _id, doc, meta in zip(ids, documents, metadatas):
            items.append({"id": _id, "document": doc, "metadata": meta, "score": None})
        self._collections[collection] = items

    def query(
        self,
        *,
        collection: str,
        embedding: List[float],
        top_k: int,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        # Semantic search not available in this stub.
        return []

    def has_collection(self, *, collection: str) -> bool:
        return collection in self._collections
