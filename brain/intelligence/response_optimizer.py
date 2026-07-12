from __future__ import annotations

"""
Module 10: Response Optimization
=================================
Optimizes resource usage by reducing unnecessary LLM calls.

Priority order:
  Memory -> Skills -> Knowledge -> Web -> LLM

If a query is matched to Memory or Skills with high confidence,
we bypass the LLM entirely (never call Ollama).
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ResponseOptimizer:
    """
    Determines if a request can bypass the LLM and be routed directly
    to a faster/cheaper local resource.
    """

    def __init__(self) -> None:
        pass

    def optimize_route(
        self,
        *,
        intent: str,
        confidence: float,
        has_local_skill: bool,
    ) -> Dict[str, Any]:
        """
        Evaluate if we can bypass Ollama/LLM.
        
        Args:
            intent: Detected intent name.
            confidence: Confidence score of the match (0.0 to 1.0).
            has_local_skill: True if there is a local skill registered for this intent.
            
        Returns:
            Dict containing:
              - 'bypass_llm': bool
              - 'target_action': str ('MEMORY' | 'SKILL' | 'KNOWLEDGE' | 'WEB' | 'LLM')
              - 'reason': str
        """
        lower_intent = intent.upper()
        
        # Companion memory / profile / timeline / reflection / goals/ habits / preferences
        memory_intents = {
            "COMPANION_REFLECT", "COMPANION_RECOMMEND", "COMPANION_PROFILE",
            "COMPANION_TIMELINE", "LIFE_MEMORY", "RECALL_MEMORY", "RECALL_NAME"
        }
        
        # Skills
        skill_intents = {
            "OPEN_APP", "OPEN_URL", "CALCULATE", "WEATHER", "SCREENSHOT",
            "SYSTEM", "CLIPBOARD", "VOLUME", "BRIGHTNESS", "FILE_SEARCH",
            "FILE", "TIME", "DATE", "NOTE_CREATE", "NOTE_SHOW", "NOTE_DELETE"
        }

        # Priority 1: Memory (if confidence >= 0.70)
        if lower_intent in memory_intents and confidence >= 0.70:
            logger.info("ResponseOptimizer: Bypassing LLM. Direct Memory route (confidence=%.2f)", confidence)
            return {
                "bypass_llm": True,
                "target_action": "MEMORY",
                "reason": f"High confidence ({confidence:.2f}) memory query for {intent}."
            }

        # Priority 2: Skills (if registered and confidence >= 0.70)
        if (lower_intent in skill_intents or has_local_skill) and confidence >= 0.70:
            logger.info("ResponseOptimizer: Bypassing LLM. Direct Skill route (confidence=%.2f)", confidence)
            return {
                "bypass_llm": True,
                "target_action": "SKILL",
                "reason": f"High confidence ({confidence:.2f}) skill query for {intent}."
            }

        # Priority 3: Knowledge (e.g. KNOWLEDGE_QUERY, if confidence >= 0.70)
        if lower_intent == "KNOWLEDGE_QUERY" and confidence >= 0.70:
            logger.info("ResponseOptimizer: Direct local Knowledge RAG route.")
            return {
                "bypass_llm": True,
                "target_action": "KNOWLEDGE",
                "reason": "Knowledge RAG query."
            }

        # Priority 4: Web Search (e.g. WEB_SEARCH or SEARCH, if confidence >= 0.70)
        if lower_intent in {"WEB_SEARCH", "SEARCH"} and confidence >= 0.70:
            logger.info("ResponseOptimizer: Direct Web Search route.")
            return {
                "bypass_llm": True,
                "target_action": "WEB",
                "reason": "Web Search query."
            }

        # Fallback to LLM (either confidence is too low or intent is GENERAL_QUERY/CHAT)
        logger.info("ResponseOptimizer: Fallback to LLM (confidence=%.2f, intent=%s)", confidence, intent)
        return {
            "bypass_llm": False,
            "target_action": "LLM",
            "reason": "Low confidence or general query needing LLM reasoning."
        }
