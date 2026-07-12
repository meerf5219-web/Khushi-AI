from __future__ import annotations

"""
Module 1: Input Normalizer
===========================
Cleans raw speech/text before any further processing.

Responsibilities:
- Normalize whitespace
- Normalize case (lowercase)
- Handle contractions
- Standardize numbers written as words
- Normalize punctuation
- Fix common speech-recognition artifacts
"""

import logging
import re
from typing import List, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Contraction expansion map
# ---------------------------------------------------------------------------
_CONTRACTIONS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bi'm\b", re.I), "i am"),
    (re.compile(r"\bi've\b", re.I), "i have"),
    (re.compile(r"\bi'll\b", re.I), "i will"),
    (re.compile(r"\bi'd\b", re.I), "i would"),
    (re.compile(r"\byou're\b", re.I), "you are"),
    (re.compile(r"\byou've\b", re.I), "you have"),
    (re.compile(r"\byou'll\b", re.I), "you will"),
    (re.compile(r"\byou'd\b", re.I), "you would"),
    (re.compile(r"\bhe's\b", re.I), "he is"),
    (re.compile(r"\bshe's\b", re.I), "she is"),
    (re.compile(r"\bit's\b", re.I), "it is"),
    (re.compile(r"\bthey're\b", re.I), "they are"),
    (re.compile(r"\bthey've\b", re.I), "they have"),
    (re.compile(r"\bthey'll\b", re.I), "they will"),
    (re.compile(r"\bwe're\b", re.I), "we are"),
    (re.compile(r"\bwe've\b", re.I), "we have"),
    (re.compile(r"\bwe'll\b", re.I), "we will"),
    (re.compile(r"\bcan't\b", re.I), "cannot"),
    (re.compile(r"\bwon't\b", re.I), "will not"),
    (re.compile(r"\bdon't\b", re.I), "do not"),
    (re.compile(r"\bdoesn't\b", re.I), "does not"),
    (re.compile(r"\bdidn't\b", re.I), "did not"),
    (re.compile(r"\bisn't\b", re.I), "is not"),
    (re.compile(r"\baren't\b", re.I), "are not"),
    (re.compile(r"\bwasn't\b", re.I), "was not"),
    (re.compile(r"\bweren't\b", re.I), "were not"),
    (re.compile(r"\bwhat's\b", re.I), "what is"),
    (re.compile(r"\bwhere's\b", re.I), "where is"),
    (re.compile(r"\bwho's\b", re.I), "who is"),
    (re.compile(r"\bhow's\b", re.I), "how is"),
    (re.compile(r"\bthat's\b", re.I), "that is"),
    (re.compile(r"\bthere's\b", re.I), "there is"),
    (re.compile(r"\blet's\b", re.I), "let us"),
]

# ---------------------------------------------------------------------------
# Word-to-digit map for common spoken numbers
# ---------------------------------------------------------------------------
_NUMBER_WORDS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bone hundred\b", re.I), "100"),
    (re.compile(r"\bfifty\b", re.I), "50"),
    (re.compile(r"\btwenty\b", re.I), "20"),
    (re.compile(r"\bten\b", re.I), "10"),
    (re.compile(r"\bnine\b", re.I), "9"),
    (re.compile(r"\beight\b", re.I), "8"),
    (re.compile(r"\bseven\b", re.I), "7"),
    (re.compile(r"\bsix\b", re.I), "6"),
    (re.compile(r"\bfive\b", re.I), "5"),
    (re.compile(r"\bfour\b", re.I), "4"),
    (re.compile(r"\bthree\b", re.I), "3"),
    (re.compile(r"\btwo\b", re.I), "2"),
    (re.compile(r"\bone\b", re.I), "1"),
    (re.compile(r"\bzero\b", re.I), "0"),
]

# Speech recognition common artifacts
_SR_ARTIFACTS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\buh-huh\b", re.I), "yes"),
    (re.compile(r"\bum+\b", re.I), ""),
    (re.compile(r"\buh+\b", re.I), ""),
    (re.compile(r"\bhm+\b", re.I), ""),
    (re.compile(r"\buhh+\b", re.I), ""),
]


class InputNormalizer:
    """
    Normalize raw text input from speech recognition or keyboard.

    All transformations are reversible in the sense that semantic meaning
    is preserved — this is NOT lossy normalization.
    """

    def normalize(self, text: str) -> str:
        if not text or not text.strip():
            return ""

        original = text
        result = text.strip()

        # 1. Remove speech recognition artifacts
        for pattern, replacement in _SR_ARTIFACTS:
            result = pattern.sub(replacement, result)

        # 2. Normalize whitespace (collapse multiple spaces/tabs/newlines)
        result = re.sub(r"\s+", " ", result).strip()

        # 3. Expand contractions
        for pattern, replacement in _CONTRACTIONS:
            result = pattern.sub(replacement, result)

        # 4. Normalize punctuation — remove duplicate punctuation
        result = re.sub(r"([?!.]){2,}", r"\1", result)
        
        # Remove commas
        result = result.replace(",", "")
        
        # Remove trailing period
        if result.endswith("."):
            result = result[:-1]

        # Remove stray punctuation at the start/end
        result = result.strip(" ;:")

        # 5. Lowercase (preserves proper nouns intact since we lowercase all)
        result = result.lower().strip()

        # 6. Normalize extra whitespace again after all transformations
        result = re.sub(r"\s+", " ", result).strip()

        if result != original.lower().strip():
            logger.debug("Normalizer: '%s' → '%s'", original, result)

        return result

