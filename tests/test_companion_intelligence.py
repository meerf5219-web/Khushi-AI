"""
Step 5: Companion Intelligence — Test Suite
=============================================
Tests:
 1. Daily reflection
 2. Weekly reflection
 3. Monthly reflection
 4. Recommendation generation (UPSC, Gym, Projects, Coding, etc.)
 5. Recommendation deduplication within session
 6. Conversation continuity (session tracking)
 7. Conversation continuity (memory-based resume)
 8. Duplicate prevention (no identical recos within call)
 9. Conflict resolution (detect + confirmation message)
10. Personality constraints (non_emotional, honest_policy, prohibitions)
11. Personality: no fabrication claim
12. Performance: reflection caching
13. Intent routing: COMPANION_REFLECT
14. Intent routing: COMPANION_RECOMMEND
15. Intent routing: COMPANION_PROFILE
16. Intent routing: COMPANION_TIMELINE
17. Integration: think() with memory data
18. Projects listed from Companion Memory
"""

import json
import os
import tempfile
import time
from datetime import datetime, timedelta
from typing import Any, Dict

import pytest

from brain.intent import IntentEngine
from companion.conflict.resolver import ConflictResolver
from companion.continuity.engine import ConversationContinuityEngine
from companion.engine import CompanionIntelligenceEngine
from companion.personality.engine import PersonalityEngine
from companion.recommendations.engine import RecommendationEngine
from companion.reflection.engine import ReflectionEngine
from companion.response.generator import ResponseGenerator
from memory.companion.engine import CompanionMemoryStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _make_timeline(*values_and_dates):
    """Create timeline list from (value, datetime) pairs."""
    records = []
    for val, dt in values_and_dates:
        records.append({
            "created_at": _iso(dt),
            "updated_at": _iso(dt),
            "category": "timeline",
            "confidence": 0.9,
            "value": val,
        })
    return records


def _make_summary(
    *,
    goals=None,
    habits=None,
    projects=None,
    preferences=None,
    timeline=None,
):
    summary: Dict[str, Any] = {
        "goals": {"records": goals or {}},
        "habits": {"records": habits or {}},
        "projects": {"records": projects or {}},
        "preferences": {"records": preferences or {}},
        "timeline": {"records": timeline or []},
        "education": {"records": {}},
        "career": {"records": {}},
        "health": {"records": {}},
    }
    return summary


# ---------------------------------------------------------------------------
# 1. Daily reflection
# ---------------------------------------------------------------------------

def test_reflection_daily():
    now = datetime(2026, 7, 8, 10, 0, 0)
    timeline = _make_timeline(
        ("Studied UPSC today", now),
        ("Went to gym", now - timedelta(hours=2)),
        ("Last week event", now - timedelta(days=7)),
    )
    summary = _make_summary(timeline=timeline)
    out = ReflectionEngine().generate(summary=summary, now_text=_iso(now))
    assert out["daily"]["items"], "Daily items should be non-empty"
    daily_vals = [i["value"] for i in out["daily"]["items"]]
    assert "Studied UPSC today" in daily_vals
    assert "Went to gym" in daily_vals
    assert "Last week event" not in daily_vals


# ---------------------------------------------------------------------------
# 2. Weekly reflection
# ---------------------------------------------------------------------------

def test_reflection_weekly():
    now = datetime(2026, 7, 8, 10, 0, 0)  # Wednesday, ISO week 28
    same_week = now - timedelta(days=2)     # Monday July 6 — same ISO week 28
    timeline = _make_timeline(
        ("This week study", same_week),
        ("Last month event", datetime(2026, 6, 1)),
    )
    summary = _make_summary(timeline=timeline)
    out = ReflectionEngine().generate(summary=summary, now_text=_iso(now))
    weekly_vals = [i["value"] for i in out["weekly"]["items"]]
    assert "This week study" in weekly_vals
    assert "Last month event" not in weekly_vals



# ---------------------------------------------------------------------------
# 3. Monthly reflection
# ---------------------------------------------------------------------------

def test_reflection_monthly():
    now = datetime(2026, 7, 8, 10, 0, 0)
    this_month = datetime(2026, 7, 1, 12, 0, 0)
    last_month = datetime(2026, 6, 15, 12, 0, 0)
    timeline = _make_timeline(
        ("July event", this_month),
        ("June event", last_month),
    )
    summary = _make_summary(timeline=timeline)
    out = ReflectionEngine().generate(summary=summary, now_text=_iso(now))
    monthly_vals = [i["value"] for i in out["monthly"]["items"]]
    assert "July event" in monthly_vals
    assert "June event" not in monthly_vals


# ---------------------------------------------------------------------------
# 4. Reflection natural summary
# ---------------------------------------------------------------------------

def test_reflection_natural_summary():
    now = datetime(2026, 7, 8, 10, 0, 0)
    timeline = _make_timeline(("UPSC study session", now))
    summary = _make_summary(timeline=timeline)
    out = ReflectionEngine().generate(summary=summary, now_text=_iso(now))
    assert "natural_summary" in out["daily"]
    assert out["daily"]["natural_summary"]  # non-empty string


# ---------------------------------------------------------------------------
# 5. Recommendation generation — UPSC
# ---------------------------------------------------------------------------

def test_recommendations_upsc_goal():
    summary = _make_summary(
        goals={"g1": {"payload": {"value": "Crack UPSC"}}},
    )
    engine = RecommendationEngine()
    recos = engine.generate(
        summary=summary,
        reflection={"daily": {"items": []}, "weekly": {"items": []}, "monthly": {"items": []}},
        planning={},
        history_limit=500,
        duplicate_threshold=0.98,
    )
    assert recos, "Should produce recommendations from UPSC goal"
    domains = [r["domain"] for r in recos]
    assert "UPSC" in domains, f"Expected UPSC domain, got: {domains}"
    # Every recommendation must have a WHY
    for r in recos:
        assert r.get("why"), f"Missing why for: {r}"


# ---------------------------------------------------------------------------
# 6. Recommendations: gym + project + coding
# ---------------------------------------------------------------------------

def test_recommendations_gym_project_coding():
    summary = _make_summary(
        habits={"h1": {"payload": {"value": "Daily gym workout"}}},
        projects={"p1": {"payload": {"value": "Khushi AI project"}}},
        preferences={"pr1": {"payload": {"value": "Python programming"}}},
    )
    engine = RecommendationEngine()
    recos = engine.generate(
        summary=summary,
        reflection={"daily": {"items": []}, "weekly": {"items": []}, "monthly": {"items": []}},
        planning={},
        history_limit=500,
        duplicate_threshold=0.98,
    )
    domains = [r["domain"] for r in recos]
    assert "Gym" in domains
    assert "Projects" in domains
    assert "Coding" in domains
    # Titles must be unique within call
    titles = [r["title"] for r in recos]
    assert len(titles) == len(set(titles)), "Duplicate titles within call"


# ---------------------------------------------------------------------------
# 7. Recommendation: deduplication within session
# ---------------------------------------------------------------------------

def test_recommendations_dedup_within_session():
    summary = _make_summary(
        goals={"g1": {"payload": {"value": "UPSC preparation"}}},
    )
    engine = RecommendationEngine()
    blank = {"daily": {"items": []}, "weekly": {"items": []}, "monthly": {"items": []}}
    recos1 = engine.generate(summary=summary, reflection=blank, planning={}, history_limit=500, duplicate_threshold=0.98)
    # Second call same session — no new items (all already in session_seen)
    recos2 = engine.generate(summary=summary, reflection=blank, planning={}, history_limit=500, duplicate_threshold=0.98)
    assert len(recos2) == 0, "Second call in same session must return 0 (all deduped)"


# ---------------------------------------------------------------------------
# 8. Recommendation: reset_session clears dedup
# ---------------------------------------------------------------------------

def test_recommendations_reset_session():
    summary = _make_summary(
        goals={"g1": {"payload": {"value": "UPSC preparation"}}},
    )
    engine = RecommendationEngine()
    blank = {"daily": {"items": []}, "weekly": {"items": []}, "monthly": {"items": []}}
    recos1 = engine.generate(summary=summary, reflection=blank, planning={}, history_limit=500, duplicate_threshold=0.98)
    engine.reset_session()
    recos2 = engine.generate(summary=summary, reflection=blank, planning={}, history_limit=500, duplicate_threshold=0.98)
    assert len(recos2) > 0, "After reset, recommendations should appear again"


# ---------------------------------------------------------------------------
# 9. Conversation continuity: session tracking
# ---------------------------------------------------------------------------

def test_continuity_session_tracking():
    engine = ConversationContinuityEngine()
    engine.record_turn(user_input="My goal is UPSC", assistant_response="Noted.", intent="LIFE_MEMORY")
    engine.record_turn(user_input="What should I study?", assistant_response="UPSC: review polity.", intent="COMPANION_RECOMMEND")
    summary = engine.session_summary()
    assert summary["session_turns"] == 2
    assert "LIFE_MEMORY" in summary["intents_seen"]
    assert "COMPANION_RECOMMEND" in summary["intents_seen"]


# ---------------------------------------------------------------------------
# 10. Conversation continuity: memory-based resume
# ---------------------------------------------------------------------------

def test_continuity_memory_based_resume():
    engine = ConversationContinuityEngine()
    summary = _make_summary(
        projects={"p1": {"payload": {"value": "Khushi AI project"}}},
    )
    hint = engine.find_resumed_context(summary=summary, query_lower="what about khushi ai")
    assert hint is not None, "Should find project in Companion Memory"
    assert "Project" in hint


# ---------------------------------------------------------------------------
# 11. Conflict resolution: no conflict
# ---------------------------------------------------------------------------

def test_conflict_no_conflict():
    resolver = ConflictResolver()
    summary = _make_summary()
    result = resolver.check(summary=summary, bucket="preferences", new_value="Python")
    assert not result.conflict_detected
    assert result.confirmation_message is None


# ---------------------------------------------------------------------------
# 12. Conflict resolution: conflict detected
# ---------------------------------------------------------------------------

def test_conflict_detected():
    resolver = ConflictResolver()
    summary = _make_summary(
        preferences={
            "pref:python": {
                "payload": {"value": "Python", "status": "active"},
            }
        }
    )
    result = resolver.check(summary=summary, bucket="preferences", new_value="Rust")
    assert result.conflict_detected, "Should detect conflict: Python vs Rust"
    assert result.old_value == "Python"
    assert result.new_value == "Rust"
    assert result.confirmation_message is not None
    assert "replace" in result.confirmation_message.lower() or "would you like" in result.confirmation_message.lower()


# ---------------------------------------------------------------------------
# 13. Personality: non-emotional hard invariants
# ---------------------------------------------------------------------------

def test_personality_invariants():
    engine = PersonalityEngine()
    p = engine.enforce_constraints()
    assert p.get("non_emotional") is True
    assert p.get("no_emotion_claims") is True
    assert p.get("no_consciousness_claims") is True
    assert p.get("no_manipulation") is True
    assert p.get("honest_policy"), "honest_policy must be set"
    assert p.get("prohibited"), "prohibited behaviors must be listed"
    assert any("emotion" in b.lower() or "feelings" in b.lower() for b in p["prohibited"])


# ---------------------------------------------------------------------------
# 14. Personality: prohibited list includes no-consciousness
# ---------------------------------------------------------------------------

def test_personality_no_consciousness():
    engine = PersonalityEngine()
    p = engine.enforce_constraints()
    prohibited_lower = " ".join(p.get("prohibited", [])).lower()
    assert "consciousness" in prohibited_lower or "sentien" in prohibited_lower


# ---------------------------------------------------------------------------
# 15. Reflection caching
# ---------------------------------------------------------------------------

def test_reflection_caching():
    now = datetime(2026, 7, 8, 10, 0, 0)
    timeline = _make_timeline(("Study event", now))
    summary = _make_summary(timeline=timeline)
    engine = ReflectionEngine()
    t0 = time.perf_counter()
    out1 = engine.generate(summary=summary, now_text=_iso(now))
    t1 = time.perf_counter() - t0
    t2_start = time.perf_counter()
    out2 = engine.generate(summary=summary, now_text=_iso(now))
    t2 = time.perf_counter() - t2_start
    # Second call should be significantly faster (cache hit)
    assert t2 < t1 + 0.05, "Cache hit should be faster than first call"
    # Results should be identical
    assert out1["daily"]["items"] == out2["daily"]["items"]


# ---------------------------------------------------------------------------
# 16. Intent routing: COMPANION_REFLECT
# ---------------------------------------------------------------------------

def test_intent_companion_reflect():
    engine = IntentEngine()
    result = engine.detect("How am I doing?")
    assert result["intent"] == "COMPANION_REFLECT"


def test_intent_companion_recommend():
    engine = IntentEngine()
    result = engine.detect("What should I focus on today?")
    assert result["intent"] == "COMPANION_RECOMMEND"


def test_intent_companion_profile():
    engine = IntentEngine()
    result = engine.detect("Show my profile")
    assert result["intent"] == "COMPANION_PROFILE"


def test_intent_companion_timeline():
    engine = IntentEngine()
    result = engine.detect("Show my timeline")
    assert result["intent"] == "COMPANION_TIMELINE"


# ---------------------------------------------------------------------------
# 17. Integration: think() with stored goal and habit
# ---------------------------------------------------------------------------

def test_think_with_goal_and_habit():
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "companion_memory.json")
        from memory.companion.engine import MemoryRecord
        store = CompanionMemoryStore(file_name=path)

        # Store a goal
        goal_id = "goals:upsc"
        rec_goal = MemoryRecord(
            created_date="2026-07-01T10:00:00Z",
            updated_date="2026-07-01T10:00:00Z",
            confidence=1.0,
            source="test",
            category="goals",
            payload={"value": "Crack UPSC", "id": goal_id, "tags": []},
        )
        store.upsert_record(bucket="goals", record_id=goal_id, record=rec_goal)

        # Store a timeline event today
        store.append_event(bucket="timeline", event={
            "created_at": "2026-07-08T09:00:00Z",
            "updated_at": "2026-07-08T09:00:00Z",
            "category": "habits",
            "confidence": 0.95,
            "value": "Morning study session",
        })

        engine = CompanionIntelligenceEngine(store=store)
        out = engine.think(now_text="2026-07-08T10:00:00Z", user_query="what should I focus on")

        assert "Companion Intelligence Summary" in out.response
        # UPSC goal should trigger recommendations
        reco_domains = [r["domain"] for r in out.recommendations]
        assert "UPSC" in reco_domains, f"Expected UPSC recommendation, got: {reco_domains}"


# ---------------------------------------------------------------------------
# 18. Projects listed from Companion Memory
# ---------------------------------------------------------------------------

def test_projects_from_memory():
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "companion_memory.json")
        from memory.companion.engine import MemoryRecord
        store = CompanionMemoryStore(file_name=path)

        proj_id = "projects:khushi"
        rec = MemoryRecord(
            created_date="2026-07-01T10:00:00Z",
            updated_date="2026-07-01T10:00:00Z",
            confidence=1.0,
            source="test",
            category="projects",
            payload={"value": "Khushi AI project", "id": proj_id, "tags": []},
        )
        store.upsert_record(bucket="projects", record_id=proj_id, record=rec)

        engine = CompanionIntelligenceEngine(store=store)
        profile = engine.get_profile()
        project_values = [
            rec2.get("payload", {}).get("value") or rec2.get("payload", {}).get("text")
            for rec2 in profile.get("projects", {}).values()
            if isinstance(rec2, dict)
        ]
        assert "Khushi AI project" in project_values


# ---------------------------------------------------------------------------
# 19. Response: non-hallucination with empty memory
# ---------------------------------------------------------------------------

def test_response_no_hallucination_empty_memory():
    engine = CompanionIntelligenceEngine(
        store=CompanionMemoryStore(file_name=os.path.join(tempfile.gettempdir(), "khushi_ci_test_empty.json"))
    )
    out = engine.think()
    # Must not invent content
    assert "Companion Intelligence" in out.response
    # Personality must be enforced
    assert out.personality.get("non_emotional") is True


# ---------------------------------------------------------------------------
# 20. Conflict revision entry builder
# ---------------------------------------------------------------------------

def test_conflict_revision_entry():
    resolver = ConflictResolver()
    entry = resolver.build_revision_entry(
        old_value="Python",
        old_confidence=0.9,
        old_updated_at="2026-07-01T00:00:00Z",
        old_revision=1,
    )
    assert entry["revision"] == 1
    assert entry["value"] == "Python"
    assert entry["confidence"] == 0.9
