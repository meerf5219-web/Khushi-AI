from __future__ import annotations

"""
Conversation Continuity Engine
===============================
Tracks session history and allows resuming previous conversations.
Grounded ONLY in CompanionMemoryStore data — never invents context.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_MAX_SESSION_TURNS = 50  # Keep per-session history bounded


@dataclass
class SessionTurn:
    """A single Q&A exchange in a session."""
    user_input: str
    assistant_response: str
    intent: str
    timestamp_unix: float = field(default_factory=time.time)


@dataclass
class ConversationContinuityEngine:
    """
    Manages conversation history within a session and references previous
    sessions via Companion Memory.

    Policy:
    - Only references what is stored in CompanionMemoryStore.
    - Never fabricates context from previous sessions.
    - Provides hooks for resuming projects, goals, unfinished work.
    """

    _session_turns: List[SessionTurn] = field(default_factory=list)

    def record_turn(self, *, user_input: str, assistant_response: str, intent: str) -> None:
        """Record a single exchange into the current session."""
        t0 = time.perf_counter()
        turn = SessionTurn(
            user_input=user_input,
            assistant_response=assistant_response,
            intent=intent,
        )
        self._session_turns.append(turn)
        if len(self._session_turns) > _MAX_SESSION_TURNS:
            self._session_turns = self._session_turns[-_MAX_SESSION_TURNS:]
        elapsed = time.perf_counter() - t0
        logger.debug("ConversationContinuity: recorded turn (%.4fs)", elapsed)

    def recent_turns(self, *, limit: int = 5) -> List[Dict[str, Any]]:
        """Return the most recent N turns as dicts."""
        turns = self._session_turns[-limit:] if limit > 0 else []
        return [
            {
                "user_input": t.user_input,
                "assistant_response": t.assistant_response,
                "intent": t.intent,
                "timestamp_unix": t.timestamp_unix,
            }
            for t in turns
        ]

    def find_resumed_context(self, *, summary: Dict[str, Any], query_lower: str) -> Optional[str]:
        """
        Scan Companion Memory for relevant context matching the user query.
        Returns a brief grounded continuation hint or None if nothing found.
        Never invents context.
        """
        t0 = time.perf_counter()

        hints: List[str] = []

        # Check projects
        projects = summary.get("projects", {}).get("records", {})
        if isinstance(projects, dict):
            for _, rec in projects.items():
                if not isinstance(rec, dict):
                    continue
                payload = rec.get("payload", {}) if isinstance(rec, dict) else {}
                val = str(payload.get("value") or payload.get("text") or "").lower()
                if val and (val in query_lower or any(w in query_lower for w in val.split()[:3])):
                    hints.append(f"Project: {payload.get('value') or payload.get('text')}")

        # Check goals
        goals = summary.get("goals", {}).get("records", {})
        if isinstance(goals, dict):
            for _, rec in goals.items():
                if not isinstance(rec, dict):
                    continue
                payload = rec.get("payload", {}) if isinstance(rec, dict) else {}
                val = str(payload.get("value") or payload.get("text") or "").lower()
                if val and (val in query_lower or any(w in query_lower for w in val.split()[:3])):
                    hints.append(f"Goal: {payload.get('value') or payload.get('text')}")

        elapsed = time.perf_counter() - t0
        logger.debug("ConversationContinuity: find_resumed_context (%.4fs), hits=%d", elapsed, len(hints))

        if hints:
            return "Continuing from Companion Memory — " + "; ".join(hints[:3])
        return None

    def session_summary(self) -> Dict[str, Any]:
        """Return a summary of the current session."""
        return {
            "session_turns": len(self._session_turns),
            "intents_seen": list({t.intent for t in self._session_turns}),
            "recent_topics": [t.user_input[:80] for t in self._session_turns[-3:]],
        }
