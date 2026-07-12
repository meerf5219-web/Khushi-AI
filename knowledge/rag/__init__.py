from __future__ import annotations

"""
Compatibility wrapper package for Phase-5 RAG architecture.

Current working code still lives in `khushi/knowledge/rag_engine.py`.
These wrapper modules introduce the new module layout without migrating
existing KnowledgeSkill pipeline yet.
"""

from knowledge.rag.rag_engine import RAGEngine

__all__ = ["RAGEngine"]
