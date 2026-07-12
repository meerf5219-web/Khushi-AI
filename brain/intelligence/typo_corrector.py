from __future__ import annotations

"""
Module 2: Typo Correction Engine
==================================
Corrects common typos from speech recognition and keyboard input.

Strategy:
- Curated correction dictionary (high-precision, domain-specific)
- Edit-distance fallback for unknown words (only when confident)
- Never aggressively modifies uncommon proper nouns or technical terms
- Confidence-based: low-confidence corrections are skipped

No external dependencies required.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Curated correction dictionary
# High-confidence, domain-specific. Never modify this without a test.
# ---------------------------------------------------------------------------
_CORRECTIONS: Dict[str, str] = {
    # Common speech recognition errors
    "ise": "is",
    "iam": "i am",
    "whats": "what is",
    "hows": "how is",
    "whos": "who is",
    "wheres": "where is",
    # Common typos
    "remeber": "remember",
    "rember": "remember",
    "remeber": "remember",
    "reember": "remember",
    "remembr": "remember",
    "favrite": "favorite",
    "favourit": "favourite",
    "favourte": "favourite",
    "favorit": "favorite",
    "favorte": "favorite",
    "favourit": "favourite",
    "wat": "what",
    "wnat": "what",
    "waht": "what",
    "nme": "name",
    "naem": "name",
    "nayme": "name",
    "nmae": "name",
    "teh": "the",
    "thhe": "the",
    "tthe": "the",
    "mmy": "my",
    "myy": "my",
    "ii": "i",
    "adn": "and",
    "nad": "and",
    "andd": "and",
    "andt": "and",
    "shwo": "show",
    "sohw": "show",
    "shoow": "show",
    "shw": "show",
    "tel": "tell",
    "tll": "tell",
    "telll": "tell",
    "opne": "open",
    "oen": "open",
    "searh": "search",
    "seach": "search",
    "saerch": "search",
    "calcualte": "calculate",
    "calculte": "calculate",
    "calclate": "calculate",
    "calculat": "calculate",
    "calulate": "calculate",
    "screenshoot": "screenshot",
    "screensot": "screenshot",
    "screenshto": "screenshot",
    "screnshot": "screenshot",
    "profiel": "profile",
    "proifle": "profile",
    "profle": "profile",
    "prolfe": "profile",
    "goalss": "goals",
    "goalls": "goals",
    "goales": "goals",
    "habist": "habits",
    "habitss": "habits",
    "habts": "habits",
    "projcts": "projects",
    "proejcts": "projects",
    "pojects": "projects",
    "projectss": "projects",
    "prefernce": "preference",
    "perference": "preference",
    "preferene": "preference",
    "prefrences": "preferences",
    "timelne": "timeline",
    "timline": "timeline",
    "timlne": "timeline",
    "companian": "companion",
    "companio": "companion",
    "comapnion": "companion",
    "memroy": "memory",
    "mmeory": "memory",
    "meomry": "memory",
    "memoyr": "memory",
    "upsc": "upsc",  # Keep as-is (acronym)
    "recomend": "recommend",
    "recomend": "recommend",
    "reccommend": "recommend",
    "recommned": "recommend",
    "reflction": "reflection",
    "refleciton": "reflection",
    "refletion": "reflection",
}

# Words that should never be auto-corrected (acronyms, proper nouns, etc.)
_PROTECTED_WORDS = {
    "upsc", "ai", "llm", "rag", "api", "url", "khushi", "faisal",
    "python", "rust", "chrome", "notepad",
}

# Edit distance threshold for auto-correction (lower = more conservative)
_MAX_EDIT_DISTANCE = 2
_MIN_WORD_LENGTH_FOR_EDIT = 5  # Don't apply edit distance to short words


def _edit_distance(a: str, b: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    # Use DP table
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            if a[i - 1] == b[j - 1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])
            prev = temp
    return dp[n]


class TypoCorrectionEngine:
    """
    Corrects common speech recognition errors and keyboard typos.

    Policy:
    - Dictionary-based corrections have priority (high precision).
    - Edit-distance fallback is conservative (min word length, max distance).
    - Protected words are never modified.
    - All corrections are logged.
    """

    def __init__(self, *, vocabulary: Optional[List[str]] = None) -> None:
        # Base vocabulary for edit-distance matching
        self._vocab: List[str] = vocabulary or list(_CORRECTIONS.values()) + [
            "what", "where", "who", "when", "why", "how",
            "show", "tell", "open", "search", "find", "remember",
            "favorite", "favourite", "profile", "timeline", "goals",
            "habits", "projects", "preferences", "memory", "reflection",
            "recommend", "companion", "calculate", "screenshot",
        ]
        # Deduplicate
        self._vocab = list(dict.fromkeys(self._vocab))

    def correct(self, text: str) -> Tuple[str, List[str]]:
        """
        Correct typos in text.

        Returns:
            (corrected_text, list_of_corrections_applied)
        """
        if not text:
            return text, []

        words = text.split()
        result_words: List[str] = []
        corrections: List[str] = []

        for word in words:
            # Strip trailing punctuation before checking
            suffix = ""
            clean = word
            if clean and clean[-1] in "?.!,;:":
                suffix = clean[-1]
                clean = clean[:-1]

            corrected = self._correct_word(clean)
            if corrected != clean:
                corrections.append(f"'{word}' → '{corrected}{suffix}'")
                logger.info("TypoCorrector: '%s' → '%s'", word, corrected + suffix)
            result_words.append(corrected + suffix)

        return " ".join(result_words), corrections

    def _correct_word(self, word: str) -> str:
        if not word:
            return word

        lower = word.lower()

        # Never correct protected words
        if lower in _PROTECTED_WORDS:
            return word

        # Dictionary lookup (exact match)
        if lower in _CORRECTIONS:
            return _CORRECTIONS[lower]

        # Skip very short words (1-3 chars) — too risky
        if len(lower) < 4:
            return word

        # Skip words that look like numbers or contain digits
        if any(c.isdigit() for c in lower):
            return word

        # Edit-distance fallback (only for longer words)
        if len(lower) >= _MIN_WORD_LENGTH_FOR_EDIT:
            best_match, best_dist = self._best_vocab_match(lower)
            if best_match and best_dist <= _MAX_EDIT_DISTANCE:
                # Additional guard: don't replace if the word looks plausible
                # (has vowels, reasonable consonant ratio)
                if self._looks_like_typo(lower) and best_dist <= 1:
                    return best_match

        return word

    def _best_vocab_match(self, word: str) -> Tuple[Optional[str], int]:
        """Find the closest vocabulary word within edit distance threshold."""
        best: Optional[str] = None
        best_dist = _MAX_EDIT_DISTANCE + 1

        for candidate in self._vocab:
            if abs(len(candidate) - len(word)) > _MAX_EDIT_DISTANCE:
                continue
            dist = _edit_distance(word, candidate)
            if dist < best_dist:
                best_dist = dist
                best = candidate

        return best, best_dist

    def _looks_like_typo(self, word: str) -> bool:
        """Heuristic: does this word look like it might be a typo?"""
        vowels = set("aeiou")
        vowel_count = sum(1 for c in word if c in vowels)
        # Very low vowel ratio suggests a typo
        if len(word) >= 4 and vowel_count == 0:
            return True
        # Consecutive same characters (3+)
        if re.search(r"(.)\1{2,}", word):
            return True
        return False
