from __future__ import annotations

import hashlib
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from config.rag import DEFAULT_COLLECTION, DOCUMENTS_DIR, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K, VECTOR_DB_PATH
from knowledge.chunker import Chunker
from knowledge.document_loader import DocumentLoader
from knowledge.embedding_manager import EmbeddingManager

from typing import TYPE_CHECKING

from knowledge.retriever import Retriever  # noqa: F401 (keeps module discoverable)

if TYPE_CHECKING:
    from knowledge.vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IndexStats:
    documents_loaded: int
    chunks_created: int
    embeddings_generated: int
    upserts: int
    total_latency: float


def _stable_doc_id(path: str) -> str:
    return hashlib.sha256(path.encode("utf-8")).hexdigest()[:16]


class KnowledgeIndexer:
    """Incremental indexer for knowledge documents.

    Incremental rule:
      - Only upsert chunks for files whose last_modified changed since last indexing.
    """

    def __init__(
        self,
        *,
        vector_store: "VectorStore",
        embedder: EmbeddingManager,
        chunker: Optional[Chunker] = None,
        collection_default: str = DEFAULT_COLLECTION,
        documents_dir: str = DOCUMENTS_DIR,
        state_path: Optional[str] = None,
    ) -> None:
        from utils.paths import get_data_dir
        
        self._vector_store = vector_store
        self._embedder = embedder
        self._chunker = chunker or Chunker()
        self._collection_default = collection_default
        self._documents_dir = documents_dir
        self._state_path = state_path or str(get_data_dir() / "knowledge" / "index_state.json")

        self._state: Dict[str, float] = {}
        self._load_state()

    def _load_state(self) -> None:
        try:
            import json

            if os.path.exists(self._state_path):
                with open(self._state_path, "r", encoding="utf-8") as f:
                    self._state = json.load(f)
            else:
                self._state = {}
        except Exception:  # pragma: no cover
            self._state = {}

    def _save_state(self) -> None:
        import json

        os.makedirs(os.path.dirname(self._state_path) or ".", exist_ok=True)
        with open(self._state_path, "w", encoding="utf-8") as f:
            json.dump(self._state, f, indent=2)

    def index(self) -> IndexStats:
        t0 = time.perf_counter()

        documents_loaded = 0
        chunks_created = 0
        embeddings_generated = 0
        upserts = 0

        updated = False

        loader = DocumentLoader(documents_dir=self._documents_dir)  # type: ignore[arg-type]

        for loaded in loader.iter_documents():
            documents_loaded += 1
            collection = loaded.collection or self._collection_default
            doc_id = _stable_doc_id(loaded.path)
            last_modified = float(loaded.last_modified)

            prev_mtime = self._state.get(doc_id)
            if prev_mtime is not None and prev_mtime >= last_modified:
                continue  # incremental: unchanged

            # Build chunks across pages.
            all_chunks: List[Tuple[str, str, Dict[str, Any]]] = []
            for page_num, page_text in loaded.text_by_page.items():
                base_meta = {
                    "collection": collection,
                    "filename": loaded.filename,
                    "path": loaded.path,
                    "page": page_num,
                    "last_modified": last_modified,
                }
                chunks = self._chunker.chunk_text(
                    text=page_text,
                    base_metadata=base_meta,
                    doc_id=f"{doc_id}_p{page_num}",
                )
                for ch in chunks:
                    all_chunks.append((ch.chunk_id, ch.text, ch.metadata))

            if not all_chunks:
                # Still mark as indexed to avoid repeated work on empty extractors.
                self._state[doc_id] = last_modified
                updated = True
                continue

            # Embed chunk texts.
            chunk_ids = [cid for cid, _, _ in all_chunks]
            chunk_texts = [txt for _, txt, _ in all_chunks]
            metadatas = [md for _, _, md in all_chunks]
            documents = chunk_texts  # store chunk text as document payload

            logger.info("Document loaded: %s (collection=%s)", loaded.path, collection)

            # Embedding latency + count
            embeddings = self._embedder.embed(chunk_texts)
            embeddings_generated += len(embeddings)

            chunks_created += len(all_chunks)

            # Upsert into vector store.
            self._vector_store.upsert(
                collection=collection,
                ids=chunk_ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
            upserts += 1

            # Update state.
            self._state[doc_id] = last_modified
            updated = True

            logger.info("Chunks created: %s (doc=%s)", len(all_chunks), loaded.path)

        if updated:
            self._save_state()

        total_latency = time.perf_counter() - t0
        return IndexStats(
            documents_loaded=documents_loaded,
            chunks_created=chunks_created,
            embeddings_generated=embeddings_generated,
            upserts=upserts,
            total_latency=total_latency,
        )
