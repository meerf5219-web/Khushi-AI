from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence


class VectorStore(ABC):
    """Compatibility interface for vector store implementations.

    NOTE: Current working implementation lives in `khushi/knowledge/vector_store.py`.
    This module is a Phase-5 wrapper-only addition.
    """

    @abstractmethod
    def upsert(
        self,
        *,
        collection: str,
        ids: Sequence[str],
        embeddings: Sequence[List[float]],
        documents: Sequence[str],
        metadatas: Sequence[Dict[str, Any]],
    ) -> None:
        """Insert or update vectors."""

    @abstractmethod
    def query(
        self,
        *,
        collection: str,
        embedding: List[float],
        top_k: int,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Return top-k matches with fields including id, document, metadata, score."""

    @abstractmethod
    def has_collection(self, *, collection: str) -> bool:
        """Return True if collection exists in this store."""
