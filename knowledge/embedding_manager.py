from __future__ import annotations

import logging
from typing import List, Optional

from config.rag import EMBEDDING_MODEL

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Generate dense embeddings using a lightweight local model."""

    def __init__(self, *, model_name: str = EMBEDDING_MODEL) -> None:
        self._model_name = model_name
        self._model = None

    def _load(self) -> None:
        if self._model is not None:
            return

        # Lazy import so the system can boot even without embedding deps.
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "Embedding model dependencies are missing. Install sentence-transformers."
            ) from exc

        self._model = SentenceTransformer(self._model_name)

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts into vectors."""
        self._load()
        # sentence-transformers returns numpy arrays; convert to python lists.
        vectors = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return [v.tolist() for v in vectors]
