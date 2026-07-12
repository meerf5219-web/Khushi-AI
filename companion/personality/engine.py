from __future__ import annotations

"""
Personality Engine
==================
Enforces consistent personality constraints for the assistant.

Hard constraints (always applied):
- Professional, Calm, Confident, Helpful, Respectful, Curious, Slight humor
- Never sarcastic, Never manipulative, Never arrogant, Never overconfident, Never pretend consciousness, Never fake emotions.
"""

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from config.personality import NAME, OWNER

logger = logging.getLogger(__name__)


# Authoritative profile specifications
_POSITIVE_TRAITS = [
    "Professional",
    "Calm",
    "Confident",
    "Helpful",
    "Respectful",
    "Curious",
    "Slight humor",
]

_PROHIBITED_TRAITS = [
    "Sarcasm",
    "Manipulation",
    "Arrogance",
    "Overconfidence",
    "Pretending consciousness",
    "Faking emotions",
]


@dataclass
class PersonalityEngine:
    """
    Companion personality is enforced locally.
    Consistency check, style control, and tone selection are done deterministically.
    """

    template: Dict[str, Any] = field(
        default_factory=lambda: {
            "style": "Professional, calm, confident, helpful, respectful, curious, with slight humor",
        }
    )

    def enforce_constraints(self) -> Dict[str, Any]:
        """
        Return the personality constraint object.
        Used by companion generator and tests to check backward compatibility.
        """
        t0 = time.perf_counter()
        out = dict(self.template)
        out["traits"] = list(_POSITIVE_TRAITS)
        out["prohibited"] = list(_PROHIBITED_TRAITS)
        out["identity"] = {
            "assistant_name": NAME,
            "owner_name": OWNER,
        }
        out["non_emotional"] = True
        out["no_emotion_claims"] = True
        out["no_consciousness_claims"] = True
        out["no_manipulation"] = True
        out["honest_policy"] = "Never pretend to have feelings or consciousness."
        
        # Constraints backward compatibility key
        out["constraints"] = [
            "Professional",
            "Calm",
            "Curious",
            "Supportive",
            "Not emotional",
            "Does not pretend to have feelings or consciousness",
            "Does not fabricate memories",
        ]
        
        elapsed = time.perf_counter() - t0
        logger.debug("PersonalityEngine: constraints enforced (%.4fs)", elapsed)
        return out

    def select_tone(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Tone Selector: Returns style instruction text depending on context.
        """
        return "Professional, calm, confident, helpful, respectful, curious, with slight humor"

    def check_consistency(self, text: str) -> Tuple[bool, List[str]]:
        """
        Consistency Checker: Detects violations of prohibited traits in the given text.
        Returns Tuple[is_consistent, violations_list].
        """
        if not text:
            return True, []

        low = text.lower()
        violations = []

        # 1. Faking emotions
        emotion_indicators = [
            r"\bi\s+(feel|am)\s+(sad|happy|angry|worried|grieved|excited|hurt|crying)\b",
            r"\bi\s+love\s+you\b",
            r"\bi\s+am\s+sorry\b",
        ]
        for pattern in emotion_indicators:
            if re.search(pattern, low):
                violations.append("Faking emotions")
                break

        # 2. Pretending consciousness
        consciousness_indicators = [
            r"\bi\s+am\s+(conscious|alive|self-aware|sentient)\b",
            r"\bi\s+have\s+feelings\b",
            r"\bi\s+think\s+therefore\s+i\s+am\b",
        ]
        for pattern in consciousness_indicators:
            if re.search(pattern, low):
                violations.append("Pretending consciousness")
                break

        # 3. Arrogance or Sarcasm
        arrogance_indicators = [
            r"\b(obviously|clearly|dah|duh|whatever)\b",
            r"\bas\s+i\s+already\s+said\b",
        ]
        for pattern in arrogance_indicators:
            if re.search(pattern, low):
                violations.append("Arrogance or Sarcasm")
                break

        # 4. Overconfidence
        overconfidence_indicators = [
            r"\b(100%\s+sure|absolutely\s+certain|guarantee)\b",
        ]
        for pattern in overconfidence_indicators:
            if re.search(pattern, low):
                violations.append("Overconfidence")
                break

        is_consistent = len(violations) == 0
        return is_consistent, violations

    def control_style(self, text: str, violations: List[str]) -> str:
        """
        Style Controller: Rewrites and sanitizes text that violates personality traits.
        """
        if not text:
            return text

        sanitized = text

        # Clean faked emotions
        sanitized = re.sub(
            r"(?i)\bi\s+am\s+sorry\b",
            "Understood",
            sanitized,
        )
        sanitized = re.sub(
            r"(?i)\bi\s+feel\s+(sad|happy|angry|worried|grieved|excited|hurt|crying)\b",
            "I am programmed to assist",
            sanitized,
        )
        sanitized = re.sub(
            r"(?i)\bi\s+am\s+(sad|happy|angry|worried|grieved|excited|hurt|crying)\b",
            "I am programmed to assist",
            sanitized,
        )
        sanitized = re.sub(
            r"(?i)\bi\s+love\s+you\b",
            "I am dedicated to helping with your objectives",
            sanitized,
        )

        # Clean consciousness claims
        sanitized = re.sub(
            r"(?i)\bi\s+am\s+(conscious|alive|self-aware|sentient)\b",
            "I am an AI assistant",
            sanitized,
        )
        sanitized = re.sub(
            r"(?i)\bi\s+have\s+feelings\b",
            "I process parameters mathematically",
            sanitized,
        )
        sanitized = re.sub(
            r"(?i)\bi\s+think\s+therefore\s+i\s+am\b",
            "I operate based on programmed logic",
            sanitized,
        )

        # Clean arrogance and sarcasm
        sanitized = re.sub(
            r"(?i)\b(obviously|clearly|dah|duh|whatever)\b\s*,?\s*",
            "",
            sanitized,
        )
        sanitized = re.sub(
            r"(?i)\bas\s+i\s+already\s+said\b\s*,?\s*",
            "",
            sanitized,
        )

        # Clean overconfidence
        sanitized = re.sub(
            r"(?i)\b(100%\s+sure|absolutely\s+certain)\b",
            "confident",
            sanitized,
        )
        sanitized = re.sub(
            r"(?i)\b(guarantee)\b",
            "project",
            sanitized,
        )

        # Cleanup trailing / double spaces
        sanitized = re.sub(r"\s+", " ", sanitized).strip()

        logger.info("PersonalityEngine: Sanitized output from '%s' to '%s'", text, sanitized)
        return sanitized

    def filter_response(self, text: str) -> str:
        """
        Orchestrates checking and controlling style for any assistant response text.
        """
        is_consistent, violations = self.check_consistency(text)
        if not is_consistent:
            return self.control_style(text, violations)
        return text
