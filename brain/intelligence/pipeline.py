from __future__ import annotations

"""
Intelligence Pipeline (Module Integration)
===========================================
Combines all 10 Modules into a single execution pipeline.

Execution flow for user text:
  1. Input Normalization (whitespace, contractions)
  2. Typo Correction (dictionary and edit-distance)
  3. Learning Engine Check (apply learned corrections, or learn new one if feedback)
  4. Query Rewriting (map natural variations to canonical intent phrases)
  5. Semantic Intent Matching (sentence-transformers similarity or keyword fallback)
  6. Confidence Evaluation (high/medium/low score tier)
  7. Ambiguity Resolution (detect and resolve ambiguous intents)
  8. Multi-Intent Parsing (detect and split compound requests)
  9. Context-Aware Routing (look up memory/recent conversation context)
 10. Response Optimization (bypass LLM/Ollama for high-confidence local actions)
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from brain.intelligence.normalizer import InputNormalizer
from brain.intelligence.typo_corrector import TypoCorrectionEngine
from brain.intelligence.query_rewriter import QueryRewriter
from brain.intelligence.semantic_matcher import SemanticIntentMatcher, SemanticMatch
from brain.intelligence.confidence_engine import ConfidenceEngine, ConfidenceResult
from brain.intelligence.multi_intent import MultiIntentParser
from brain.intelligence.ambiguity_resolver import AmbiguityResolver, AmbiguityResult
from brain.intelligence.context_router import ContextRouter
from brain.intelligence.learning_engine import LearningEngine
from brain.intelligence.response_optimizer import ResponseOptimizer

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    original_query: str
    normalized_query: str
    typo_corrections: List[str]
    corrected_query: str
    rewritten_query: str
    rewriter_rule: Optional[str]
    semantic_match: Optional[SemanticMatch]
    confidence: ConfidenceResult
    is_multi_intent: bool
    sub_queries: List[str]
    ambiguity: AmbiguityResult
    contextual_response: Optional[str]
    optimization: Dict[str, Any]
    latency_ms: float
    routing_intent: str
    routing_reason: str


class IntelligencePipeline:
    """
    Main coordinator for the Intelligence Layer.
    """

    def __init__(self, *, cie: Optional[Any] = None, context_manager: Optional[Any] = None) -> None:
        self.normalizer = InputNormalizer()
        self.typo_corrector = TypoCorrectionEngine()
        self.rewriter = QueryRewriter()
        self.semantic_matcher = SemanticIntentMatcher()
        self.confidence_engine = ConfidenceEngine()
        self.multi_parser = MultiIntentParser()
        self.ambiguity_resolver = AmbiguityResolver()
        self.context_router = ContextRouter(cie=cie, context_manager=context_manager)
        self.learning_engine = LearningEngine()
        self.optimizer = ResponseOptimizer()
        
        from brain.conversation_understanding.engine import NaturalConversationEngine
        self.conversation_engine = NaturalConversationEngine()

    def process(self, text: str, recent_turns: Optional[List[Dict[str, Any]]] = None) -> PipelineResult:
        """
        Process user input query through all 10 intelligence modules.
        """
        t0 = time.perf_counter()
        recent_turns = recent_turns or []

        # 1. Normalize
        normalized = self.normalizer.normalize(text)

        # 2. Correct typos
        corrected, corrections = self.typo_corrector.correct(normalized)

        # Apply learned corrections
        corrected_query = self.learning_engine.get_corrected_query(corrected)

        # Stateful conversation handling (indirect intents, ellipsis, acknowledgements, repairs)
        conv_query, direct_response = self.conversation_engine.process_turn(corrected_query, recent_turns)

        # 4. Rewrite using conversational-processed query
        rewritten, rule_name = self.rewriter.rewrite(conv_query)

        # 5. Semantic Match
        match = self.semantic_matcher.best_match(rewritten)
        
        # 6. Confidence Engine
        semantic_score = match.score if match else 0.0
        suggested_intent = match.intent if match else None
        
        # Context availability for confidence boost
        context_available = False
        if suggested_intent in {"COMPANION_TIMELINE", "LIFE_MEMORY_PROJECTS"}:
            context_available = True

        confidence = self.confidence_engine.evaluate(
            semantic_score=semantic_score,
            rewriter_matched=rule_name is not None,
            typo_corrected=len(corrections) > 0,
            suggested_intent=suggested_intent,
            context_available=context_available
        )

        # 7. Ambiguity Resolution
        top_matches = []
        if match:
            # fetch top matches to check score proximity
            all_matches = self.semantic_matcher.match(rewritten, top_k=2)
            top_matches = [(m.intent, m.score) for m in all_matches]
        ambiguity = self.ambiguity_resolver.resolve(rewritten, top_matches=top_matches)

        # 8. Multi-Intent Parsing
        is_multi, sub_queries = self.multi_parser.parse(rewritten)

        # 9. Context-Aware Routing
        contextual_resp = direct_response or self.context_router.route_contextually(rewritten, recent_turns)

        # 10. Response Optimization
        routing_intent = match.routing_intent if match else "CHAT"
        optimization = self.optimizer.optimize_route(
            intent=routing_intent,
            confidence=confidence.score,
            has_local_skill=True  # skills are registered in DecisionEngine
        )

        latency_ms = (time.perf_counter() - t0) * 1000

        # Log details
        logger.info(
            "IntelligencePipeline: query='%s' → normalized='%s' → intent=%s conf=%.2f route=%s latency=%.1fms",
            text, normalized, routing_intent, confidence.score, optimization["target_action"], latency_ms
        )

        return PipelineResult(
            original_query=text,
            normalized_query=normalized,
            typo_corrections=corrections,
            corrected_query=corrected_query,
            rewritten_query=rewritten,
            rewriter_rule=rule_name,
            semantic_match=match,
            confidence=confidence,
            is_multi_intent=is_multi,
            sub_queries=sub_queries,
            ambiguity=ambiguity,
            contextual_response=contextual_resp,
            optimization=optimization,
            latency_ms=latency_ms,
            routing_intent=routing_intent,
            routing_reason=f"Pipeline determined route={optimization['target_action']} via {confidence.reason}"
        )
