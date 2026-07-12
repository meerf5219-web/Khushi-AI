from __future__ import annotations

"""
Intelligence Layer — Package Init
===================================
Phase 6: Intelligent routing pipeline.

Flow:
  raw text
    → InputNormalizer
    → TypoCorrectionEngine
    → QueryRewriter
    → SemanticIntentMatcher
    → ConfidenceEngine
    → MultiIntentParser
    → AmbiguityResolver
    → ContextRouter
    → PipelineResult

The pipeline augments (never replaces) the existing IntentEngine.
"""

from brain.intelligence.pipeline import IntelligencePipeline, PipelineResult

__all__ = ["IntelligencePipeline", "PipelineResult"]
