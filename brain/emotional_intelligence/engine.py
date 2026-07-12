from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class EmotionalState:
    primary_emotion: str
    intensity: float
    stress: float
    frustration: float
    motivation: float
    celebration: float
    burnout: float
    confidence: float
    detected_keywords: List[str]


# Intensifier multipliers
_INTENSIFIERS = {
    "very": 1.3,
    "so": 1.2,
    "extremely": 1.5,
    "really": 1.2,
    "terribly": 1.4,
    "highly": 1.3,
    "absolutely": 1.4,
    "completely": 1.4,
}


class EmotionalIntelligenceEngine:
    """
    Recognizes human emotions, stress, frustration, burnout, celebration, and confidence.
    Personalizes responses using Companion Memory data.
    Strictly follows non-emotional AI response boundaries.
    """

    def __init__(self) -> None:
        # Pattern mappings for each dimension
        self._patterns = {
            "sadness": [
                (r"\b(fail|failed|loss|lost|lose)\b", 0.7),
                (r"\b(sad|unhappy|depressed|lonely|down|grief)\b", 0.6),
                (r"\b(cry|crying|tears)\b", 0.8),
                (r"\b(worst|terrible|horrible|bad)\b", 0.5),
            ],
            "stress": [
                (r"\b(stress|stressed|stressful|anxious|anxiety|worried|nervous)\b", 0.7),
                (r"\b(overwhelm|overwhelmed|overwhelming|pressure)\b", 0.8),
                (r"\b(scared|afraid|fear)\b", 0.6),
            ],
            "frustration": [
                (r"\b(stuck|annoyed|annoying|frustrated|frustrating|bother)\b", 0.7),
                (r"\b(cannot\s+do\s+this|can't\s+do\s+this|impossible|give\s+up)\b", 0.8),
                (r"\b(hate|stupid|idiot|annoy)\b", 0.6),
            ],
            "motivation": [
                (r"\b(motivated|inspire|inspired|inspiration|determined|positive)\b", 0.7),
                (r"\b(will\s+win|will\s+crack|will\s+succeed|achieve)\b", 0.8),
                (r"\b(ready|focused|focusing|excited)\b", 0.6),
            ],
            "celebration": [
                (r"\b(passed|won|success|succeeded|celebrate|celebration)\b", 0.8),
                (r"\b(yes|did\s+it|achieved|victory|milestone)\b", 0.7),
                (r"\b(happy|glad|proud|great\s+news|awesome|amazing)\b", 0.5),
            ],
            "burnout": [
                (r"\b(burnout|burnt\s+out|burned\s+out|exhausted|drained)\b", 0.8),
                (r"\b(tired|sleepy|fatigue|sleep|rest)\b", 0.6),
                (r"\b(quit|stop|cannot\s+continue|can't\s+continue|too\s+much)\b", 0.7),
            ],
            "confidence": [
                (r"\b(confident|sure|certain|believe\s+in\s+myself)\b", 0.7),
                (r"\b(easy|simple|got\s+this|can\s+do\s+it)\b", 0.6),
                (r"\b(doubt|unsure|uncertain|hesitant)\b", -0.5),  # negative confidence
            ],
        }

    def analyze_text(self, text: str) -> EmotionalState:
        """
        Analyze text to compute scores for emotional dimensions and primary emotion.
        """
        if not text or not text.strip():
            return EmotionalState(
                primary_emotion="neutral",
                intensity=0.0,
                stress=0.0,
                frustration=0.0,
                motivation=0.0,
                celebration=0.0,
                burnout=0.0,
                confidence=0.0,
                detected_keywords=[],
            )

        lower_text = text.lower()
        words = lower_text.split()

        # Check for intensifiers before keywords
        multiplier = 1.0
        for i, word in enumerate(words):
            if word in _INTENSIFIERS:
                # If there's a next word, apply multiplier
                multiplier = max(multiplier, _INTENSIFIERS[word])

        scores = {k: 0.0 for k in self._patterns}
        detected = []

        for category, patterns in self._patterns.items():
            for pattern, base_score in patterns:
                matches = re.findall(pattern, lower_text)
                if matches:
                    score_val = base_score * multiplier
                    # Clip positive/negative boundaries
                    if base_score > 0:
                        scores[category] = min(1.0, scores[category] + score_val)
                    else:
                        scores[category] = max(-1.0, scores[category] + score_val)
                    
                    for m in matches:
                        if isinstance(m, tuple):
                            detected.extend(list(m))
                        else:
                            detected.append(m)

        # Confidence is on 0 to 1 scale, adjust negative scores
        conf_raw = scores.get("confidence", 0.0)
        # Factor in motivation (boosts confidence) and stress/frustration (reduces confidence)
        confidence = max(
            0.0,
            min(
                1.0,
                0.5 + conf_raw 
                + 0.2 * scores.get("motivation", 0.0) 
                - 0.15 * scores.get("frustration", 0.0) 
                - 0.1 * scores.get("stress", 0.0)
            )
        )

        # Primary emotion is the category with highest positive score
        # (excluding confidence itself)
        candidates = {k: v for k, v in scores.items() if k != "confidence"}
        primary = max(candidates, key=candidates.get)
        
        # If the highest score is 0, primary is neutral
        if candidates[primary] <= 0.15:
            primary = "neutral"

        detected_clean = list(dict.fromkeys([d for d in detected if d]))

        state = EmotionalState(
            primary_emotion=primary,
            intensity=min(1.0, candidates.get(primary, 0.0)),
            stress=scores.get("stress", 0.0),
            frustration=scores.get("frustration", 0.0),
            motivation=scores.get("motivation", 0.0),
            celebration=scores.get("celebration", 0.0),
            burnout=scores.get("burnout", 0.0),
            confidence=confidence,
            detected_keywords=detected_clean,
        )

        logger.info(
            "EmotionalState: primary=%s intensity=%.2f stress=%.2f frustration=%.2f burnout=%.2f motivation=%.2f celebration=%.2f confidence=%.2f",
            state.primary_emotion, state.intensity, state.stress, state.frustration, state.burnout, state.motivation, state.celebration, state.confidence
        )

        return state

    def personalize_response(
        self,
        state: EmotionalState,
        query: str,
        profile_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Generate a personalized emotional support/coaching response based on memory profile.
        Returns None if no specific personalization template applies.
        """
        profile = profile_data or {}
        goals = []
        projects = []

        # Extract goals from profile
        goal_records = profile.get("goals", {})
        if isinstance(goal_records, dict):
            for rec in goal_records.values():
                val = rec.get("payload", {}).get("value")
                if val:
                    goals.append(val)

        # Extract projects from profile
        project_records = profile.get("projects", {})
        if isinstance(project_records, dict):
            for rec in project_records.values():
                val = rec.get("payload", {}).get("value")
                if val:
                    projects.append(val)

        # Case 1: Failure or sadness detected + goal present
        if state.primary_emotion == "sadness" and state.intensity > 0.4:
            # Check context overlap with query
            low_query = query.lower()
            if "exam" in low_query or "test" in low_query or "fail" in low_query:
                # Find matching target goal
                target_goal = None
                for g in goals:
                    if any(w in g.lower() for w in ["upsc", "exam", "test", "study"]):
                        target_goal = g
                        break
                if not target_goal and goals:
                    target_goal = goals[0]

                if target_goal:
                    return (
                        f"I know the attempt for '{target_goal}' is important. "
                        "Let's review the outcome, isolate the weak areas, and adjust the study plan for the next attempt."
                    )
                return (
                    "Failing an attempt is part of the process. "
                    "Let's review the specific problem areas and plan adjustments to the next strategy."
                )

        # Case 2: Frustration or Burnout detected + project/goal present
        if (state.burnout > 0.5 or state.frustration > 0.5) and state.intensity > 0.4:
            active_subject = None
            if projects:
                active_subject = projects[0]
            elif goals:
                active_subject = goals[0]

            if active_subject:
                return (
                    f"Working on '{active_subject}' can be demanding. "
                    "A structured pause is a valid strategic tool. "
                    "Let's schedule a rest period and simplify the next milestones."
                )
            return (
                "High demands often lead to fatigue. "
                "A structured rest period is recommended. "
                "Let's simplify current action items."
            )

        # Case 3: Celebration detected + project/goal present
        if state.primary_emotion == "celebration" and state.intensity > 0.4:
            active_subject = None
            # Match project word in query
            low_query = query.lower()
            for p in projects:
                if any(w in p.lower() for w in low_query.split()):
                    active_subject = p
                    break
            if not active_subject and projects:
                active_subject = projects[0]

            if active_subject:
                return (
                    f"This is a constructive milestone for '{active_subject}'. "
                    "Let's record this achievement in the timeline and outline the next steps."
                )
            return (
                "Constructive milestone achieved. "
                "Let's record the progress in the timeline and identify the next milestones."
            )

        return None
