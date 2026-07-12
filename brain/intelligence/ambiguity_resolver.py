from __future__ import annotations

"""
Module 7: Ambiguity Resolver
==============================
Detects when a query has multiple valid interpretations and
generates a clarification question.

Example:
  "Open office."
    → Could be: Microsoft Office | Office document | The office (location)
    → Ask: "Did you mean Microsoft Office, an Office file, or something else?"

Policy:
- Only flags ambiguity when multiple semantically distinct matches exist
  with close confidence scores (within the ambiguity_threshold).
- Single clear winner → not ambiguous.
- Protected domain words that are always unambiguous (e.g., "upsc").
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# How close two top scores need to be to be considered ambiguous
_AMBIGUITY_THRESHOLD = 0.08

# Ambiguous keyword patterns: keyword → possible interpretations
_AMBIGUOUS_PHRASES: Dict[str, List[str]] = {
    "office": ["Microsoft Office", "an Office document", "the office location"],
    "chrome": ["Google Chrome browser", "the Chrome app"],
    "mail": ["your email app", "physical mail"],
    "notes": ["your saved notes", "Apple Notes", "audio notes"],
    "calendar": ["your calendar app", "Google Calendar"],
    "map": ["Maps app", "a specific map"],
    "music": ["your music player", "a music file"],
    "terminal": ["Command Prompt", "PowerShell", "a terminal app"],
    "open": None,  # context-dependent — don't resolve independently
}


@dataclass
class AmbiguityResult:
    is_ambiguous: bool
    clarification_question: Optional[str]
    interpretations: List[str]


class AmbiguityResolver:
    """
    Detects ambiguous queries and generates clarification questions.

    Only asks for clarification when:
    1. A known ambiguous keyword is present, OR
    2. Two semantic matches have very close scores (within threshold)
    """

    def resolve(
        self,
        text: str,
        *,
        top_matches: Optional[List[Tuple[str, float]]] = None,
    ) -> AmbiguityResult:
        """
        Check if text is ambiguous.

        Args:
            text: Normalized user query.
            top_matches: Optional list of (intent, score) from SemanticMatcher.

        Returns:
            AmbiguityResult with is_ambiguous, clarification_question, interpretations.
        """
        lower = text.lower().strip()

        # 1. Check known ambiguous keywords
        for keyword, interpretations in _AMBIGUOUS_PHRASES.items():
            if interpretations is None:
                continue
            # Only flag if the entire query is just this keyword (or "open X")
            if re.match(rf"^(open|launch|start)?\s*{keyword}\.?$", lower):
                question = f"Did you mean {', '.join(interpretations[:-1])}, or {interpretations[-1]}?"
                logger.info("AmbiguityResolver: '%s' is ambiguous → %s", text, question)
                return AmbiguityResult(
                    is_ambiguous=True,
                    clarification_question=question,
                    interpretations=interpretations,
                )

        # 2. Check if top semantic matches are too close
        if top_matches and len(top_matches) >= 2:
            score_diff = abs(top_matches[0][1] - top_matches[1][1])
            # Both scores must be above a minimum threshold (above 0.5) to be meaningful
            if (
                score_diff < _AMBIGUITY_THRESHOLD
                and top_matches[0][1] > 0.5
                and top_matches[1][1] > 0.5
            ):
                i1 = top_matches[0][0].replace("_", " ").title()
                i2 = top_matches[1][0].replace("_", " ").title()
                question = f"Did you mean to {i1.lower()} or {i2.lower()}?"
                logger.info("AmbiguityResolver: close scores %s", question)
                return AmbiguityResult(
                    is_ambiguous=True,
                    clarification_question=question,
                    interpretations=[i1, i2],
                )

        return AmbiguityResult(
            is_ambiguous=False,
            clarification_question=None,
            interpretations=[],
        )


import re  # noqa: E402 — imported after class for use in method
