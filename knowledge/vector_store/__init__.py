"""
Phase 5 vector_store *package* compatibility layer.

Re-exports all symbols from the legacy module `knowledge._vector_store_legacy`
so that any code doing `from knowledge.vector_store import ChromaVectorStore`
continues to work without modification.
"""

from __future__ import annotations

# Import from the renamed legacy module (avoids circular import)
from knowledge._vector_store_legacy import (
    ChromaVectorStore,
    InMemoryVectorStore,
    VectorStore,
    get_vector_store,
)

__all__ = [
    "VectorStore",
    "ChromaVectorStore",
    "InMemoryVectorStore",
    "get_vector_store",
]
