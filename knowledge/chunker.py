from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from config.rag import CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Chunk:
    """A text chunk plus retrieval metadata."""

    chunk_id: str
    text: str
    metadata: Dict[str, Any]


class Chunker:
    """Chunk documents into overlapping windows for semantic retrieval."""

    def __init__(self, *, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be >= 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be < chunk_size")

        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def chunk_text(
        self,
        *,
        text: str,
        base_metadata: Dict[str, Any],
        doc_id: str,
    ) -> List[Chunk]:
        """Create overlapping chunks and attach required metadata."""
        cleaned = (text or "").strip()
        if not cleaned:
            return []

        # Simple character-based chunking to remain dependency-light.
        # Future upgrades can switch to sentence/token chunking without breaking interfaces.
        step = self._chunk_size - self._chunk_overlap
        chunks: List[Chunk] = []

        start = 0
        idx = 0
        while start < len(cleaned):
            end = min(len(cleaned), start + self._chunk_size)
            chunk_text = cleaned[start:end].strip()
            if chunk_text:
                chunk_id = f"{doc_id}_chunk_{idx}"
                metadata = dict(base_metadata)
                metadata["chunk_id"] = chunk_id
                chunks.append(Chunk(chunk_id=chunk_id, text=chunk_text, metadata=metadata))

            idx += 1
            if end == len(cleaned):
                break
            start += step

        logger.info("Chunks created: %s for doc_id=%s", len(chunks), doc_id)
        return chunks
