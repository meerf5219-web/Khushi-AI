from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional, Protocol, Sequence, Tuple

from config.rag import VECTOR_DB_BACKEND, VECTOR_DB_PATH, DEFAULT_COLLECTION

logger = logging.getLogger(__name__)


class VectorStore(ABC):
    """Abstract vector store interface for semantic retrieval."""

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


# --------- Chroma Implementation (default) ---------
try:
    import chromadb  # type: ignore
    from chromadb.config import Settings  # type: ignore
except Exception:  # pragma: no cover
    chromadb = None  # type: ignore


class ChromaVectorStore(VectorStore):
    """ChromaDB-backed VectorStore implementation."""

    def __init__(self, *, path: str = VECTOR_DB_PATH) -> None:
        if chromadb is None:
            raise RuntimeError("chromadb is not installed.")

        # Keep settings conservative and local-only.
        self._client = chromadb.PersistentClient(path=path, settings=Settings(allow_reset=True))
        self._collections: Dict[str, Any] = {}

    def _get_collection(self, *, collection: str):
        if collection not in self._collections:
            self._collections[collection] = self._client.get_or_create_collection(name=collection)
        return self._collections[collection]

    def upsert(
        self,
        *,
        collection: str,
        ids: Sequence[str],
        embeddings: Sequence[List[float]],
        documents: Sequence[str],
        metadatas: Sequence[Dict[str, Any]],
    ) -> None:
        col = self._get_collection(collection=collection)
        col.upsert(
            ids=list(ids),
            embeddings=list(embeddings),
            documents=list(documents),
            metadatas=list(metadatas),
        )

    def query(
        self,
        *,
        collection: str,
        embedding: List[float],
        top_k: int,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        col = self._get_collection(collection=collection)
        res = col.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=metadata_filter or None,
            include=["metadatas", "documents", "distances", "ids"],
        )

        # Chroma returns lists for each query.
        results: List[Dict[str, Any]] = []
        metadatas = res.get("metadatas", [[]])[0]
        documents = res.get("documents", [[]])[0]
        ids = res.get("ids", [[]])[0]
        distances = res.get("distances", [[]])[0]

        for i in range(len(ids)):
            score = None
            if i < len(distances) and distances[i] is not None:
                # Chroma distance: lower is better. Convert to a generic score.
                score = 1.0 / (1.0 + float(distances[i]))
            results.append(
                {
                    "id": ids[i],
                    "document": documents[i],
                    "metadata": metadatas[i],
                    "score": score,
                }
            )
        return results

    def has_collection(self, *, collection: str) -> bool:
        try:
            self._client.get_collection(name=collection)
            return True
        except Exception:
            return False


class InMemoryVectorStore(VectorStore):
    """In-memory fallback vector store used when optional deps are missing.

    This implementation is intentionally minimal: it supports the interface
    but returns no matches so the app can run without chromadb.
    """

    def __init__(self) -> None:
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
        # Store only metadata/documents for potential future expansion.
        # (Embeddings are ignored in this fallback.)
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
        # No semantic search available without embeddings backend.
        # Return empty list to keep behavior safe (no hallucination).
        return []

    def has_collection(self, *, collection: str) -> bool:
        return collection in self._collections


# --------- Factory ---------
def get_vector_store(*, backend: str = VECTOR_DB_BACKEND) -> VectorStore:
    """Create a configured vector store implementation."""
    if backend == "chroma":
        if chromadb is None:
            logger.warning("chromadb is not installed; using InMemoryVectorStore fallback.")
            return InMemoryVectorStore()
        return ChromaVectorStore(path=VECTOR_DB_PATH)

    raise RuntimeError(f"Unsupported VECTOR_DB_BACKEND={backend}.")
