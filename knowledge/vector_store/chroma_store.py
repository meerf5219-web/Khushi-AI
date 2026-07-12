from __future__ import annotations

"""
Compatibility wrapper for Chroma-backed vector store.

Current working implementation lives in `khushi/knowledge/vector_store.py`.
This module is Phase-5 wrapper-only addition.
"""

from typing import Any, Dict, List, Optional, Sequence

from config.rag import VECTOR_DB_PATH
from knowledge.vector_store.base import VectorStore



def _load_legacy_module():
    """Load the legacy `knowledge/_vector_store_legacy` module.

    Uses a direct Python import which works in both development and
    frozen PyInstaller builds. The spec_from_file_location pattern
    is intentionally avoided as it requires a raw .py file on disk
    which does not exist in PyInstaller bundles.
    """
    from knowledge import _vector_store_legacy
    return _vector_store_legacy


def _legacy_import():
    legacy = _load_legacy_module()
    return legacy.ChromaVectorStore, legacy.get_vector_store



class ChromaVectorStore(VectorStore):
    """Compatibility wrapper around legacy ChromaVectorStore (behavior-preserving)."""

    def __init__(self, *, path: str = VECTOR_DB_PATH) -> None:
        LegacyChromaVectorStore, _ = _legacy_import()
        self._impl = LegacyChromaVectorStore(path=path)

    def upsert(
        self,
        *,
        collection: str,
        ids: Sequence[str],
        embeddings: Sequence[List[float]],
        documents: Sequence[str],
        metadatas: Sequence[Dict[str, Any]],
    ) -> None:
        self._impl.upsert(
            collection=collection,
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def query(
        self,
        *,
        collection: str,
        embedding: List[float],
        top_k: int,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        return self._impl.query(
            collection=collection,
            embedding=embedding,
            top_k=top_k,
            metadata_filter=metadata_filter,
        )

    def has_collection(self, *, collection: str) -> bool:
        return self._impl.has_collection(collection=collection)


def get_vector_store(*, backend: str = "chroma"):
    """Compatibility re-export (lazy)."""
    _, legacy_get_vector_store = _legacy_import()
    # Legacy signature in `knowledge/vector_store.py` supports `backend` only.
    return legacy_get_vector_store(backend=backend)  # type: ignore[arg-type]
