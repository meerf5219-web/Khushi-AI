from __future__ import annotations

"""
Module 5: Confidence Engine
=============================
Assigns a confidence score to every routing decision and determines the
routing strategy.

Tiers:
  HIGH   (≥ 0.95): Route directly to skill/memory. No LLM needed.
  MEDIUM (0.70 – 0.94): Route with IntentEngine; optionally confirm.
  LOW    (< 0.70):  Fallback to Knowledge → Web → LLM.

Sources of confidence:
  1. Semantic similarity score from SemanticMatcher
  2. Query rewriter match (rule-based = high confidence)
  3. Typo correction quality
  4. Context availability from Companion Memory
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# Thresholds
HIGH_CONFIDENCE = 0.95
MEDIUM_CONFIDENCE = 0.70


@dataclass
class ConfidenceResult:
    score: float
    level: str          # "high" | "medium" | "low"
    reason: str
    route_directly: bool        # True = skip IntentEngine, use suggested_intent
    use_llm: bool               # True = this query should go to LLM
    suggested_intent: Optional[str]


class ConfidenceEngine:
    """
    Determines routing confidence and strategy.

    Inputs:
    - semantic_score: from SemanticIntentMatcher (0.0–1.0)
    - rewriter_matched: True if QueryRewriter applied a rule
    - typo_corrected: True if TypoCorrector made changes
    - suggested_intent: from SemanticMatcher
    - context_available: True if Companion Memory has relevant context
    """

    def evaluate(
        self,
        *,
        semantic_score: float,
        rewriter_matched: bool,
        typo_corrected: bool,
        suggested_intent: Optional[str],
        context_available: bool = False,
    ) -> ConfidenceResult:
        t_start = __import__("time").perf_counter()

        score = semantic_score

        # Boost for rule-based rewrites (high precision)
        if rewriter_matched:
            score = min(1.0, score + 0.15)

        # Small boost for context availability
        if context_available:
            score = min(1.0, score + 0.05)

        # Small penalty if typo correction was needed (less certain)
        if typo_corrected:
            score = max(0.0, score - 0.03)

        # Determine level
        if score >= HIGH_CONFIDENCE:
            level = "high"
            route_directly = True
            use_llm = False
        elif score >= MEDIUM_CONFIDENCE:
            level = "medium"
            route_directly = False
            use_llm = False
        else:
            level = "low"
            route_directly = False
            use_llm = True

        # If no intent suggested and score is low → must use LLM
        if not suggested_intent:
            use_llm = level == "low"
            route_directly = False

        # Memory/profile intents with high score should never need LLM
        memory_intents = {
            "COMPANION_REFLECT", "COMPANION_RECOMMEND", "COMPANION_PROFILE",
            "COMPANION_TIMELINE", "LIFE_MEMORY", "RECALL_MEMORY",
            "RECALL_NAME", "NOTE_SHOW", "NOTE_CREATE",
        }
        if suggested_intent in memory_intents and score >= MEDIUM_CONFIDENCE:
            use_llm = False

        reason = (
            f"semantic={semantic_score:.2f} "
            f"rewriter={rewriter_matched} "
            f"typo={typo_corrected} "
            f"context={context_available} "
            f"→ final={score:.2f} ({level})"
        )

        elapsed = __import__("time").perf_counter() - t_start
        logger.info(
            "ConfidenceEngine: %s intent=%s use_llm=%s route_direct=%s (%.4fs)",
            reason, suggested_intent, use_llm, route_directly, elapsed,
        )

        return ConfidenceResult(
            score=score,
            level=level,
            reason=reason,
            route_directly=route_directly,
            use_llm=use_llm,
            suggested_intent=suggested_intent,
        )
