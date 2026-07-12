from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional, Tuple

from config.rag import DEFAULT_COLLECTION, DOCUMENTS_DIR, VECTOR_DB_BACKEND, VECTOR_DB_PATH, FEATURE_KNOWLEDGE_ENGINE_V2
from knowledge.embedding_manager import EmbeddingManager
from knowledge.indexer import KnowledgeIndexer
from knowledge.rag_engine import RAGEngine
from knowledge.retriever import Retriever

logger = logging.getLogger(__name__)


class KnowledgeSkill:
    """Knowledge Base skill: retrieve relevant chunks and return grounded response.

    Architecture:
      KnowledgeSkill -> Retriever -> RAGEngine -> LLM Provider
    """

    def __init__(
        self,
        *,
        default_collection: str = DEFAULT_COLLECTION,
    ) -> None:
        self._default_collection = default_collection

        # V2 routing layer (default OFF). Keep legacy members intact when OFF.
        self._v2_engine = None
        if FEATURE_KNOWLEDGE_ENGINE_V2:
            from knowledge.v2.engine import KnowledgeEngineV2

            self._v2_engine = KnowledgeEngineV2()
            return

        self._embedder = EmbeddingManager()

        # Import the legacy vector store module directly (normal Python import,
        # works correctly in both development and frozen PyInstaller builds).
        from knowledge._vector_store_legacy import get_vector_store
        self._vector_store = get_vector_store(backend=VECTOR_DB_BACKEND)

        self._retriever = Retriever(
            vector_store=self._vector_store,
            embedder=self._embedder,
            default_collection=default_collection,
        )

        self._rag_engine = RAGEngine()

        self._indexer = KnowledgeIndexer(
            vector_store=self._vector_store,
            embedder=self._embedder,
            documents_dir=DOCUMENTS_DIR,
        )

    def execute(
        self,
        text: str,
        *,
        collection: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Answer using knowledge documents with strict source attribution."""
        if self._v2_engine is not None:
            answer, _trace = self._v2_engine.answer(
                query=text,
                collection=collection or self._default_collection,
                metadata_filter=metadata_filter,
            )
            return answer

        t0 = time.perf_counter()

        # Incremental indexing (only upserts changed files).
        try:
            stats = self._indexer.index()
            logger.info(
                "RAG indexing stats: documents_loaded=%s chunks_created=%s embeddings_generated=%s upserts=%s total_latency=%.3fs",
                stats.documents_loaded,
                stats.chunks_created,
                stats.embeddings_generated,
                stats.upserts,
                stats.total_latency,
            )
        except Exception as exc:
            # Do not crash the assistant.
            logger.warning("RAG incremental indexing failed: %s", exc)

        # Retrieve.
        matches, retrieval_latency = self._retriever.retrieve(
            query=text,
            collection=collection or self._default_collection,
            metadata_filter=metadata_filter,
        )
        logger.info("Retrieval latency: %.3fs", retrieval_latency)

        # Grounded generation.
        answer, trace = self._rag_engine.generate_answer(query=text, matches=matches)
        total_latency = time.perf_counter() - t0
        logger.info("Total RAG latency: %.3fs", total_latency)

        return answer
