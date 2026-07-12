from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from providers.ollama_provider import OllamaProvider
from config.rag import TOP_K

logger = logging.getLogger(__name__)


class RAGEngine:
    """Retrieve + grounded generation with strict source attribution."""

    def __init__(self, *, provider: Optional[OllamaProvider] = None) -> None:
        self._provider = provider or OllamaProvider()

    def generate_answer(
        self,
        *,
        query: str,
        matches: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> tuple[str, Dict[str, Any]]:
        """
        Returns:
          (answer_text, trace)
        trace includes generation latency and selected sources.
        """
        metadata = metadata or {}
        t0 = time.perf_counter()

        # Build grounded context from top matches.
        sources: List[Dict[str, Any]] = []
        context_blocks: List[str] = []

        for i, m in enumerate(matches[:TOP_K], start=1):
            chunk_id = (m.get("metadata") or {}).get("chunk_id") or m.get("id") or f"chunk_{i}"
            file_path = (m.get("metadata") or {}).get("path") or ""
            collection = (m.get("metadata") or {}).get("collection") or ""
            filename = (m.get("metadata") or {}).get("filename") or ""
            page = (m.get("metadata") or {}).get("page") or "N/A"
            chunk_text = m.get("document") or m.get("text") or ""

            sources.append(
                {
                    "document": filename,
                    "collection": collection,
                    "page": page,
                    "chunk_id": chunk_id,
                    "path": file_path,
                }
            )
            context_blocks.append(
                f"[Source {i} | Document={filename} | Collection={collection} | Page={page} | Chunk={chunk_id}]\n{chunk_text}"
            )

        # No matches => grounded response without calling LLM (avoids hallucination).
        if not context_blocks:
            answer = "I couldn't find relevant information in your knowledge documents."
            trace = {
                "generation_latency": 0.0,
                "sources": [],
                "used": False,
            }
            return answer, trace

        prompt = self._build_prompt(query=query, context="\n\n".join(context_blocks), metadata=metadata)

        gen_t0 = time.perf_counter()
        response = self._provider.generate(prompt, context={"query": query, **metadata})
        generation_latency = time.perf_counter() - gen_t0

        answer = (response or "").strip()

        # Ensure source attribution is always appended.
        answer_with_sources = self._append_sources(answer, sources)

        total_latency = time.perf_counter() - t0
        logger.info("Generation latency: %.3fs", generation_latency)
        logger.info("Total RAG latency: %.3fs", total_latency)

        trace = {
            "generation_latency": generation_latency,
            "total_latency": total_latency,
            "sources": sources,
            "used": True,
        }
        return answer_with_sources, trace

    def _build_prompt(self, *, query: str, context: str, metadata: Dict[str, Any]) -> str:
        return (
            "You are Khushi AI. Answer the user's question using ONLY the provided sources.\n"
            "Rules:\n"
            "- If the sources do not contain the answer, say you couldn't find it.\n"
            "- Keep the answer concise and helpful.\n"
            "- Do not invent document titles, pages, or quotes.\n\n"
            f"User question:\n{query}\n\n"
            f"Sources:\n{context}\n"
        )

    def _append_sources(self, answer: str, sources: List[Dict[str, Any]]) -> str:
        lines: List[str] = []
        lines.append(answer)
        lines.append("\n\nSources:")
        for idx, s in enumerate(sources, start=1):
            lines.append(
                f"- Document: {s.get('document')} | Collection: {s.get('collection')} | Page: {s.get('page')} | Chunk: {s.get('chunk_id')}"
            )
        return "\n".join(lines)
