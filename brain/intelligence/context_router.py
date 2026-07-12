from __future__ import annotations

"""
Module 8: Context-Aware Routing
=================================
Resolves contextual queries by using Companion Memory and recent conversation.

Examples:
- "What was my goal?" -> Retrieve goals from Companion Memory
- "What project?" -> Retrieve current active projects
- "When did I start it?" -> Check the active project/topic, then look up its start/creation event in the timeline
"""

import logging
from typing import Any, Dict, List, Optional
from companion.engine import CompanionIntelligenceEngine
from brain.context import ContextManager

logger = logging.getLogger(__name__)

class ContextRouter:
    """
    Routes queries contextually using recent conversation and Companion Memory.
    """

    def __init__(
        self,
        *,
        cie: Optional[CompanionIntelligenceEngine] = None,
        context_manager: Optional[ContextManager] = None
    ) -> None:
        self._cie = cie or CompanionIntelligenceEngine()
        self._context_manager = context_manager

    def route_contextually(self, query: str, recent_turns: List[Dict[str, Any]]) -> Optional[str]:
        """
        Check if the query can be resolved contextually.
        If it's asking for a specific memory item like a goal or project or timeline start,
        we can construct a direct answer or route it.
        
        Returns:
            A resolved response string if handled contextually, else None.
        """
        lower_query = query.lower().strip()
        
        # 1. Handle "What was my goal?" / "What is my goal?"
        if any(p in lower_query for p in ["what was my goal", "what is my goal", "my goal is what"]):
            profile = self._cie.get_profile()
            goals = profile.get("goals", {})
            if goals:
                goal_list = []
                for g in goals.values():
                    val = g.get("payload", {}).get("value")
                    if val:
                        goal_list.append(val)
                if goal_list:
                    return f"Your stored goals: {', '.join(goal_list)}."
            return "I don't have any goals saved in your Companion Memory yet."

        # 2. Handle "What project?" / "What is my project?" / "What project am I working on?"
        if any(p in lower_query for p in ["what project", "my project", "working on"]):
            profile = self._cie.get_profile()
            projects = profile.get("projects", {})
            if projects:
                proj_list = []
                for p in projects.values():
                    val = p.get("payload", {}).get("value") or p.get("payload", {}).get("text")
                    if val:
                        proj_list.append(val)
                if proj_list:
                    return f"You are working on: {', '.join(proj_list)}."
            return "I don't see any projects in your Companion Memory."

        # 3. Handle "When did I start it?" / "When did I start that?" / "When was it created?"
        if any(p in lower_query for p in ["when did i start it", "when did i start that", "when was it created", "when did i start"]):
            # Find the active project/goal from recent context
            active_topic = None
            if self._context_manager:
                active_topic = self._context_manager.last_topic
            
            # If not in context manager, inspect recent turns
            if not active_topic and recent_turns:
                for turn in reversed(recent_turns):
                    user_in = turn.get("user_input", "").lower()
                    if "project" in user_in or "goal" in user_in:
                        # try to find topic words
                        words = turn.get("user_input", "").split()
                        if len(words) > 2:
                            active_topic = " ".join(words[2:])
                            break
            
            # If we still don't have it, look at the projects in memory
            if not active_topic:
                profile = self._cie.get_profile()
                projects = profile.get("projects", {})
                if projects:
                    # use the first project's value
                    for p in projects.values():
                        active_topic = p.get("payload", {}).get("value") or p.get("payload", {}).get("text")
                        if active_topic:
                            break

            if active_topic:
                timeline = self._cie.get_timeline()
                # Search timeline for the topic
                topic_lower = active_topic.lower()
                for event in reversed(timeline): # Chronological or reversed depending on engine
                    val = str(event.get("value", "")).lower()
                    payload_val = str(event.get("payload", {}).get("value", "")).lower()
                    if topic_lower in val or topic_lower in payload_val or any(w in val for w in topic_lower.split() if len(w) > 3):
                        created_at = event.get("created_at") or event.get("created_date")
                        # Format timestamp nicely
                        if created_at:
                            return f"You started '{active_topic}' on {created_at}."
                
                # If not found in timeline but is in projects, return project created date
                profile = self._cie.get_profile()
                projects = profile.get("projects", {})
                for p in projects.values():
                    val = p.get("payload", {}).get("value") or p.get("payload", {}).get("text")
                    if val and topic_lower in val.lower():
                        created_at = p.get("created_date") or p.get("created_at")
                        if created_at:
                            return f"You started '{val}' on {created_at}."
                
                return f"I know about '{active_topic}', but I couldn't find a start date in my memory."

            return "I am not sure which project or goal you are referring to."

        return None
