from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from config.rag import DEFAULT_COLLECTION, TOP_K
from knowledge.embedding_manager import EmbeddingManager

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from knowledge.vector_store import VectorStore

logger = logging.getLogger(__name__)


class Retriever:
    """Retrieve relevant chunks from a vector store."""

    def __init__(
        self,
        *,
        vector_store: "VectorStore",
        embedder: EmbeddingManager,
        default_collection: str = DEFAULT_COLLECTION,
        top_k: int = TOP_K,
    ) -> None:
        self._vector_store = vector_store
        self._embedder = embedder
        self._default_collection = default_collection
        self._top_k = top_k

    def retrieve(
        self,
        *,
        query: str,
        collection: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> tuple[List[Dict[str, Any]], float]:
        """
        Returns:
          (matches, latency_seconds)
        matches items contain:
          document, metadata, score, id
        """
        col = collection or self._default_collection
        t0 = time.perf_counter()

        embedding = self._embedder.embed([query])[0]
        matches = self._vector_store.query(
            collection=col,
            embedding=embedding,
            top_k=self._top_k,
            metadata_filter=metadata_filter,
        )

        latency = time.perf_counter() - t0
        logger.info("Retrieval latency: %.3fs", latency)
        return matches, latency
