from __future__ import annotations

"""
Companion Intelligence Engine
==============================
Orchestrates: Reflection → Recommendation → Response

Architecture:
  CompanionMemory
       ↓
  ReflectionEngine   (analyzes timeline, goals, habits, projects)
       ↓
  RecommendationEngine  (generates grounded personalized recommendations)
       ↓
  ResponseGenerator  (formats into professional, non-emotional response)

All data sourced from CompanionMemoryStore ONLY. No external calls.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from config.companion import DUPLICATE_THRESHOLD, HISTORY_LIMIT
from memory.companion.engine import CompanionMemoryStore
from companion.reflection.engine import ReflectionEngine
from companion.recommendations.engine import RecommendationEngine
from companion.response.generator import ResponseGenerator
from companion.personality.engine import PersonalityEngine
from companion.planning.engine import PlanningEngine
from companion.continuity.engine import ConversationContinuityEngine
from companion.conflict.resolver import ConflictResolver


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CompanionOutput:
    personality: Dict[str, Any]
    reflection: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    response: str


class CompanionIntelligenceEngine:
    """
    Production-grade Companion Intelligence Engine (Step 5).

    Grounding policy:
    - Uses only CompanionMemoryStore data.
    - Never claims external facts (web/documents/LLM knowledge).
    - If memory lacks required fields, returns safe "insufficient data" messages.

    Features:
    - Daily/Weekly/Monthly Reflection
    - Personalized Recommendations with WHY
    - Conversation Continuity (session-level)
    - Duplicate Prevention (within session)
    - Conflict Resolution (with confirmation prompt)
    - Personality Constraints (enforced locally)
    - Performance caching (in ReflectionEngine)
    - Structured logging with timing
    """

    def __init__(
        self,
        *,
        store: Optional[CompanionMemoryStore] = None,
        personality_engine: Optional[PersonalityEngine] = None,
        reflection_engine: Optional[ReflectionEngine] = None,
        recommendation_engine: Optional[RecommendationEngine] = None,
        planning_engine: Optional[PlanningEngine] = None,
        response_generator: Optional[ResponseGenerator] = None,
        continuity_engine: Optional[ConversationContinuityEngine] = None,
        conflict_resolver: Optional[ConflictResolver] = None,
    ) -> None:
        self._store = store or CompanionMemoryStore()
        self._personality = personality_engine or PersonalityEngine()
        self._reflection = reflection_engine or ReflectionEngine()
        self._recommendations = recommendation_engine or RecommendationEngine()
        self._planning = planning_engine or PlanningEngine()
        self._response = response_generator or ResponseGenerator()
        self._continuity = continuity_engine or ConversationContinuityEngine()
        self._conflict = conflict_resolver or ConflictResolver()

    # ------------------------------------------------------------------
    # Core think() method
    # ------------------------------------------------------------------

    def _summary(self) -> Dict[str, Any]:
        return self._store.get_summary()

    def think(
        self,
        *,
        now_text: Optional[str] = None,
        user_query: Optional[str] = None,
    ) -> CompanionOutput:
        """
        Main reasoning cycle:
        1. Load summary from Companion Memory.
        2. Enforce personality constraints.
        3. Generate reflection (with caching).
        4. Generate planning context.
        5. Generate recommendations (dedup).
        6. Resolve conversation continuity hint.
        7. Build response.
        8. Record turn in session history.
        """
        t0 = time.perf_counter()
        summary = self._summary()

        # 1. Personality constraints
        personality = self._personality.enforce_constraints()

        # 2. Reflection
        reflection_t0 = time.perf_counter()
        reflection = self._reflection.generate(summary=summary, now_text=now_text)
        logger.info("think(): reflection (%.4fs)", time.perf_counter() - reflection_t0)

        # 3. Planning
        plan_t0 = time.perf_counter()
        planning = self._planning.generate(summary=summary, reflection=reflection)
        logger.info("think(): planning (%.4fs)", time.perf_counter() - plan_t0)

        # 4. Recommendations
        reco_t0 = time.perf_counter()
        recommendations = self._recommendations.generate(
            summary=summary,
            reflection=reflection,
            planning=planning,
            history_limit=HISTORY_LIMIT,
            duplicate_threshold=DUPLICATE_THRESHOLD,
        )
        logger.info("think(): recommendations count=%d (%.4fs)", len(recommendations), time.perf_counter() - reco_t0)

        # 5. Conversation continuity hint
        continuity_hint: Optional[str] = None
        if user_query:
            continuity_hint = self._continuity.find_resumed_context(
                summary=summary,
                query_lower=user_query.lower(),
            )

        # 6. Generate response
        response_t0 = time.perf_counter()
        response = self._response.generate(
            personality=personality,
            reflection=reflection,
            recommendations=recommendations,
            planning=planning,
            continuity_hint=continuity_hint,
        )
        logger.info("think(): response length=%d (%.4fs)", len(response), time.perf_counter() - response_t0)

        # 7. Record in session continuity
        self._continuity.record_turn(
            user_input=user_query or "(think)",
            assistant_response=response[:200],
            intent="COMPANION_THINK",
        )

        total_elapsed = time.perf_counter() - t0
        logger.info("think(): total (%.4fs)", total_elapsed)

        return CompanionOutput(
            personality=personality,
            reflection=reflection,
            recommendations=recommendations,
            response=response,
        )

    # ------------------------------------------------------------------
    # Conflict resolution API
    # ------------------------------------------------------------------

    def check_conflict(
        self,
        *,
        bucket: str,
        new_value: str,
        record_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Check if storing new_value in bucket would conflict with existing data.
        Returns a confirmation message if conflict detected, else None.
        """
        t0 = time.perf_counter()
        summary = self._summary()
        result = self._conflict.check(
            summary=summary,
            bucket=bucket,
            new_value=new_value,
            record_id=record_id,
        )
        elapsed = time.perf_counter() - t0
        if result.conflict_detected:
            logger.info(
                "check_conflict: CONFLICT bucket=%s old='%s' new='%s' (%.4fs)",
                bucket, result.old_value, new_value, elapsed,
            )
            return result.confirmation_message
        logger.debug("check_conflict: no conflict bucket=%s (%.4fs)", bucket, elapsed)
        return None

    # ------------------------------------------------------------------
    # Convenience methods for direct intent handlers
    # ------------------------------------------------------------------

    def get_reflection(self, *, now_text: Optional[str] = None) -> Dict[str, Any]:
        """Return just the reflection data (for dedicated reflection queries)."""
        t0 = time.perf_counter()
        summary = self._summary()
        result = self._reflection.generate(summary=summary, now_text=now_text)
        logger.info("get_reflection(): (%.4fs)", time.perf_counter() - t0)
        return result

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Return just the recommendations (for dedicated recommendation queries)."""
        t0 = time.perf_counter()
        summary = self._summary()
        reflection = self._reflection.generate(summary=summary)
        planning = self._planning.generate(summary=summary, reflection=reflection)
        result = self._recommendations.generate(
            summary=summary,
            reflection=reflection,
            planning=planning,
            history_limit=HISTORY_LIMIT,
            duplicate_threshold=DUPLICATE_THRESHOLD,
        )
        logger.info("get_recommendations(): count=%d (%.4fs)", len(result), time.perf_counter() - t0)
        return result

    def get_profile(self) -> Dict[str, Any]:
        """Return a structured profile from Companion Memory."""
        t0 = time.perf_counter()
        summary = self._summary()
        profile = {
            "identity": summary.get("identity", {}).get("records", {}),
            "goals": summary.get("goals", {}).get("records", {}),
            "projects": summary.get("projects", {}).get("records", {}),
            "habits": summary.get("habits", {}).get("records", {}),
            "preferences": summary.get("preferences", {}).get("records", {}),
            "education": summary.get("education", {}).get("records", {}),
            "career": summary.get("career", {}).get("records", {}),
            "health": summary.get("health", {}).get("records", {}),
        }
        logger.info("get_profile(): (%.4fs)", time.perf_counter() - t0)
        return profile

    def get_timeline(self) -> List[Dict[str, Any]]:
        """Return chronological timeline events from Companion Memory."""
        t0 = time.perf_counter()
        summary = self._summary()
        records = summary.get("timeline", {}).get("records", [])
        if not isinstance(records, list):
            records = []
        # Return newest-first
        result = list(reversed(records))
        logger.info("get_timeline(): events=%d (%.4fs)", len(result), time.perf_counter() - t0)
        return result

    def session_summary(self) -> Dict[str, Any]:
        """Return current session information."""
        return self._continuity.session_summary()

    def reset_recommendation_session(self) -> None:
        """Start a new recommendation session (clears duplicate tracking)."""
        self._recommendations.reset_session()
        logger.info("CompanionIntelligenceEngine: recommendation session reset")
