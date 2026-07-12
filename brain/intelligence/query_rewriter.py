from __future__ import annotations

"""
Module 3: Query Rewriter
=========================
Rewrites equivalent user queries into canonical forms understood by IntentEngine.

This ensures that natural, varied expressions all map to the same intent.

Examples:
  "Who am I?"           → "what is my name"
  "Tell me my name."    → "what is my name"
  "My objective."       → "show my goals"
  "The goal I told you" → "show my goals"
  "How am I doing?"     → "how am i doing"  (already an intent phrase)

Policy:
- Only rewrites when highly confident (pattern-matched).
- Never rewrites domain-specific content the user clearly intends.
- Logs every rewrite for debugging.
"""

import logging
import re
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Rewrite rules: (pattern, canonical_form, description)
# Order matters — more specific patterns first.
# ---------------------------------------------------------------------------
_REWRITE_RULES: List[Tuple[re.Pattern, str, str]] = [
    # --- Identity / Name ---
    (re.compile(r"^who\s+am\s+i\??$", re.I), "show my profile", "who am i → profile"),
    (re.compile(r"^tell\s+me\s+my\s+name\.?$", re.I), "what is my name", "tell me my name → recall name"),
    (re.compile(r"^what\s+(was|were)\s+my\s+name\.?$", re.I), "what is my name", "what was my name → recall name"),
    (re.compile(r"^what\s+(did\s+i\s+tell\s+you\s+(my|the)\s+)?name\s+(was|is).*$", re.I), "what is my name", "what did I tell you my name → recall name"),
    (re.compile(r"^(what'?s|what\s+is)\s+my\s+name\??$", re.I), "what is my name", "what is my name"),

    # --- Goals ---
    (re.compile(r"^(my\s+)?objective(s)?\.?$", re.I), "show my goals", "objective → goals"),
    (re.compile(r"^(my\s+)?goal(s)?\??\.?$", re.I), "show my goals", "my goals shorthand"),
    (re.compile(r"^(the\s+)?goal(s)?\s+(i\s+told\s+you|you\s+know(about)?).*$", re.I), "show my goals", "goal I told you → show goals"),
    (re.compile(r"^what\s+(are|is|were)\s+my\s+goal(s)?\??$", re.I), "show my goals", "what are my goals"),
    (re.compile(r"^(show|display|list|tell\s+me)\s+(my\s+)?goal(s)?\??$", re.I), "show my goals", "show goals"),
    (re.compile(r"^what\s+(is|was|are)\s+my\s+(objective|aim|target)(s)?\??$", re.I), "show my goals", "objective → goals"),

    # --- Projects ---
    (re.compile(r"^(my\s+)?project(s)?\??\.?$", re.I), "show my projects", "my projects shorthand"),
    (re.compile(r"^(show|display|list)\s+(me\s+)?(my\s+)?project(s)?\??$", re.I), "show my projects", "show projects"),
    (re.compile(r"^what\s+project(s)?\s+(am\s+i|are\s+you)\s+working\s+on\??$", re.I), "what projects am i working on", "what projects working on"),
    (re.compile(r"^(the\s+)?project\s+(i\s+was|i\s+am|i\s+told\s+you)\s+(working\s+on)?.*$", re.I), "what projects am i working on", "project I was working on → projects"),

    # --- Habits ---
    (re.compile(r"^(my\s+)?habit(s)?\??\.?$", re.I), "show my habits", "my habits shorthand"),
    (re.compile(r"^(show|list)\s+(my\s+)?habit(s)?\??$", re.I), "show my habits", "show habits"),

    # --- Preferences ---
    (re.compile(r"^(my\s+)?preference(s)?\??\.?$", re.I), "show my preferences", "my preferences shorthand"),
    (re.compile(r"^(show|list)\s+(my\s+)?preference(s)?\??$", re.I), "show my preferences", "show preferences"),

    # --- Timeline ---
    (re.compile(r"^(my\s+)?timeline\.?$", re.I), "show my timeline", "my timeline shorthand"),
    (re.compile(r"^(show|display)\s+(my\s+)?timeline\.?$", re.I), "show my timeline", "show timeline"),
    (re.compile(r"^(my\s+)?(life\s+)?history\.?$", re.I), "show my timeline", "my history → timeline"),

    # --- Profile ---
    (re.compile(r"^(my\s+)?profile\.?$", re.I), "show my profile", "my profile shorthand"),
    (re.compile(r"^(show|display)\s+(my\s+)?profile\.?$", re.I), "show my profile", "show profile"),
    (re.compile(r"^tell\s+me\s+about\s+myself\.?$", re.I), "show my profile", "tell me about myself → profile"),

    # --- Reflection ---
    (re.compile(r"^how\s+am\s+i\s+doing\??$", re.I), "how am i doing", "how am i doing → reflection"),
    (re.compile(r"^(give\s+me\s+a?\s*)?reflection\.?$", re.I), "how am i doing", "reflection"),
    (re.compile(r"^(review|summarize)\s+my\s+(progress|week|day|month)\.?$", re.I), "how am i doing", "review my progress → reflection"),

    # --- Recommendations ---
    (re.compile(r"^what\s+should\s+i\s+(do|work\s+on|study|focus\s+on)(\s+today)?\??$", re.I), "what should i focus on today", "what should I do → recommend"),
    (re.compile(r"^(give\s+me\s+a?\s*)?recommendation(s)?\.?$", re.I), "what should i focus on today", "recommendation → recommend"),
    (re.compile(r"^(my\s+)?next\s+step(s)?\.?$", re.I), "what is my next step", "next step → recommend"),

    # --- Greeting shortcuts ---
    (re.compile(r"^(good\s+)?(morning|evening|afternoon|night)\.?$", re.I), "hello", "greeting → hello"),

    # --- Memory recall shortcuts ---
    (re.compile(r"^(tell\s+me\s+)?the\s+name\s+i\s+told\s+you\.?$", re.I), "what is my name", "name I told you → recall"),
    (re.compile(r"^(what\s+is|tell\s+me)\s+the\s+goal\s+i\s+(told\s+you|mentioned)\.?$", re.I), "show my goals", "goal I told you → goals"),
]


class QueryRewriter:
    """
    Rewrites natural user queries into canonical intent phrases.

    Only applies rewrites when a rule matches with high confidence.
    Falls through transparently if no rule matches.
    """

    def rewrite(self, text: str) -> Tuple[str, Optional[str]]:
        """
        Attempt to rewrite text into a canonical form.

        Returns:
            (rewritten_text, rule_description_or_None)
        """
        if not text:
            return text, None

        stripped = text.strip().rstrip("?.!,")

        for pattern, canonical, description in _REWRITE_RULES:
            if pattern.match(stripped):
                logger.info("QueryRewriter: '%s' → '%s' [rule: %s]", text, canonical, description)
                return canonical, description

        return text, None
