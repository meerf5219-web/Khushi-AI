from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from knowledge.indexer import KnowledgeIndexer
from knowledge.embedding_manager import EmbeddingManager
from knowledge.retriever import Retriever
from knowledge.rag_engine import RAGEngine
from knowledge.vector_store import get_vector_store

logger = logging.getLogger(__name__)


class KnowledgeEngineV2:
    """
    Experimental Knowledge Engine V2 (milestone stub).

    IMPORTANT:
    - This module is intentionally a thin delegator to the legacy pipeline.
    - It ensures V2 can be toggled on/off without changing answer formatting or behavior.
    - The real modular implementation (hybrid retrieval, keyword retrieval, ranking,
      caching, etc.) will be implemented in later milestones.
    """

    def __init__(self) -> None:
        self._embedder = EmbeddingManager()
        self._vector_store = get_vector_store()

        self._retriever = Retriever(
            vector_store=self._vector_store,
            embedder=self._embedder,
        )
        self._rag_engine = RAGEngine()
        self._indexer = KnowledgeIndexer(
            vector_store=self._vector_store,
            embedder=self._embedder,
        )

    def answer(
        self,
        *,
        query: str,
        collection: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Returns:
          (answer_text, trace)
        """
        # Keep legacy behavior (including incremental indexing) intact.
        self._indexer.index()

        matches, retrieval_latency = self._retriever.retrieve(
            query=query,
            collection=collection,
            metadata_filter=metadata_filter,
        )

        answer, trace = self._rag_engine.generate_answer(
            query=query,
            matches=matches,
            metadata={
                "collection": collection or "default",
                "retrieval_latency": retrieval_latency,
            },
        )

        return answer, trace
