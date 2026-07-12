from __future__ import annotations

"""
Phase 6: Intelligence Layer - Test Suite
==========================================
Tests:
- Input Normalizer (contraction expansion, whitespace cleaning)
- Typo Correction (dictionary and edit distance matches)
- Query Rewriting (canonical mapping of questions)
- Semantic Similarity / Keyword Fallback Matching
- Confidence Scoring (evaluation of score level and routes)
- Multi-Intent Parsing (splitting joint queries)
- Ambiguity Resolution (clarification triggers)
- Context-Aware Routing (goals, projects, timeline lookup)
- Learning Engine Corrections (feedback persistence and application)
"""

import os
import json
import tempfile
import pytest
from typing import Any, Dict

from brain.intelligence.normalizer import InputNormalizer
from brain.intelligence.typo_corrector import TypoCorrectionEngine
from brain.intelligence.query_rewriter import QueryRewriter
from brain.intelligence.semantic_matcher import SemanticIntentMatcher
from brain.intelligence.confidence_engine import ConfidenceEngine
from brain.intelligence.multi_intent import MultiIntentParser
from brain.intelligence.ambiguity_resolver import AmbiguityResolver
from brain.intelligence.context_router import ContextRouter
from brain.intelligence.learning_engine import LearningEngine
from brain.intelligence.pipeline import IntelligencePipeline
from companion.engine import CompanionIntelligenceEngine
from memory.companion.engine import CompanionMemoryStore


# ---------------------------------------------------------------------------
# 1. Input Normalizer Tests
# ---------------------------------------------------------------------------
def test_normalizer():
    norm = InputNormalizer()
    assert norm.normalize("What    is   my name") == "what is my name"
    assert norm.normalize("I'm fine, thanks.") == "i am fine thanks"
    assert norm.normalize("Don't do it!!!") == "do not do it!"
    assert norm.normalize("uh-huh, okay") == "yes okay"


# ---------------------------------------------------------------------------
# 2. Typo Correction Tests
# ---------------------------------------------------------------------------
def test_typo_corrector():
    corrector = TypoCorrectionEngine()
    
    # Dict corrections
    text, corrs = corrector.correct("what ise my name")
    assert text == "what is my name"
    assert "ise" in corrs[0]
    
    text, corrs = corrector.correct("wat is my nme")
    assert text == "what is my name"
    
    text, corrs = corrector.correct("remeber my goal")
    assert text == "remember my goal"
    
    # Protected words
    text, corrs = corrector.correct("upsc is hard")
    assert text == "upsc is hard"
    assert not corrs


# ---------------------------------------------------------------------------
# 3. Query Rewriting Tests
# ---------------------------------------------------------------------------
def test_query_rewriter():
    rewriter = QueryRewriter()
    
    assert rewriter.rewrite("Who am I?")[0] == "show my profile"
    assert rewriter.rewrite("Tell me my name.")[0] == "what is my name"
    assert rewriter.rewrite("The goal I told you.")[0] == "show my goals"
    assert rewriter.rewrite("My projects.")[0] == "show my projects"
    assert rewriter.rewrite("How am I doing?")[0] == "how am i doing"


# ---------------------------------------------------------------------------
# 4. Semantic Matching Tests
# ---------------------------------------------------------------------------
def test_semantic_matcher():
    matcher = SemanticIntentMatcher()
    
    # Test best match (either via transformer or fallback keyword)
    match = matcher.best_match("What is my name?")
    assert match is not None
    assert match.routing_intent in {"RECALL_MEMORY", "LIFE_MEMORY"}
    
    match2 = matcher.best_match("open chrome browser")
    assert match2 is not None
    assert match2.routing_intent == "OPEN_APP"


# ---------------------------------------------------------------------------
# 5. Confidence Scoring Tests
# ---------------------------------------------------------------------------
def test_confidence_engine():
    engine = ConfidenceEngine()
    
    # High score
    res_high = engine.evaluate(
        semantic_score=0.98,
        rewriter_matched=True,
        typo_corrected=False,
        suggested_intent="OPEN_APP"
    )
    assert res_high.level == "high"
    assert res_high.route_directly is True
    assert res_high.use_llm is False
    
    # Low score
    res_low = engine.evaluate(
        semantic_score=0.30,
        rewriter_matched=False,
        typo_corrected=True,
        suggested_intent="GENERAL_QUERY"
    )
    assert res_low.level == "low"
    assert res_low.use_llm is True


# ---------------------------------------------------------------------------
# 6. Multi-Intent Parsing Tests
# ---------------------------------------------------------------------------
def test_multi_intent_parser():
    parser = MultiIntentParser()
    
    is_multi, parts = parser.parse("Open Chrome and tell me today's weather.")
    assert is_multi is True
    assert len(parts) == 2
    assert "open chrome" in parts[0].lower()
    assert "weather" in parts[1].lower()
    
    is_multi2, parts2 = parser.parse("Remember my goal and show my timeline.")
    assert is_multi2 is True
    assert len(parts2) == 2


# ---------------------------------------------------------------------------
# 7. Ambiguity Resolution Tests
# ---------------------------------------------------------------------------
def test_ambiguity_resolver():
    resolver = AmbiguityResolver()
    
    res = resolver.resolve("Open office")
    assert res.is_ambiguous is True
    assert "Microsoft Office" in res.clarification_question
    
    # Scores too close
    res2 = resolver.resolve("test", top_matches=[("OPEN_APP", 0.88), ("OPEN_URL", 0.86)])
    assert res2.is_ambiguous is True


# ---------------------------------------------------------------------------
# 8. Learning Engine Tests
# ---------------------------------------------------------------------------
def test_learning_engine():
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "learning_corrections.json")
        engine = LearningEngine(filepath=path)
        
        # Test correction detection
        assert engine.is_correction("No, I meant my UPSC goal") is True
        assert engine.extract_correction_target("No, I meant my UPSC goal") == "my upsc goal"
        
        # Test learning
        success, msg = engine.learn("my objective", "No, I meant my UPSC goal")
        assert success is True
        assert engine.get_corrected_query("my objective") == "my upsc goal"


# ---------------------------------------------------------------------------
# 9. Context-Aware Routing Tests
# ---------------------------------------------------------------------------
def test_context_router():
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "companion_memory.json")
        from memory.companion.engine import MemoryRecord
        store = CompanionMemoryStore(file_name=path)
        
        # Store active project
        proj_id = "projects:test"
        rec = MemoryRecord(
            created_date="2026-07-01T10:00:00Z",
            updated_date="2026-07-01T10:00:00Z",
            confidence=1.0,
            source="test",
            category="projects",
            payload={"value": "Khushi AI Project", "id": proj_id},
        )
        store.upsert_record(bucket="projects", record_id=proj_id, record=rec)
        
        # Store timeline event
        store.append_event(bucket="timeline", event={
            "created_at": "2026-07-01T10:00:00Z",
            "updated_at": "2026-07-01T10:00:00Z",
            "category": "timeline",
            "confidence": 1.0,
            "value": "Started working on Khushi AI Project",
        })
        
        cie = CompanionIntelligenceEngine(store=store)
        router = ContextRouter(cie=cie)
        
        # 1. Ask what project
        resp = router.route_contextually("what project am i working on", [])
        assert "Khushi AI Project" in resp
        
        # 2. Ask when did I start it
        resp2 = router.route_contextually("when did i start it", [])
        assert "2026-07-01T10:00:00Z" in resp2
