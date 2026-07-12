from __future__ import annotations

"""
Module 9: Learning Engine
===========================
Learns from user corrections (e.g., "No, I meant my UPSC goal").

Features:
- Detects correction patterns: "no, i meant...", "no, meant..."
- Extracts correction target.
- Maps the previous query to the corrected query or intent.
- Persists corrections to a JSON file.
- Checks learned corrections before routing.
- Never overwrites existing mappings without confirmation.
"""

import json
import logging
import os
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

from utils.paths import get_data_dir
CORRECTIONS_FILE = str(get_data_dir() / "learning_corrections.json")


class LearningEngine:
    """
    Learns routing corrections dynamically from user feedback.
    """

    def __init__(self, filepath: str = CORRECTIONS_FILE) -> None:
        self._filepath = filepath
        self._corrections: Dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._filepath):
            try:
                with open(self._filepath, "r", encoding="utf-8") as f:
                    self._corrections = json.load(f)
                logger.info("LearningEngine: Loaded %d corrections from %s", len(self._corrections), self._filepath)
            except Exception as e:
                logger.error("LearningEngine: Error loading corrections: %s", e)
                self._corrections = {}
        else:
            self._corrections = {}

    def _save(self) -> None:
        try:
            with open(self._filepath, "w", encoding="utf-8") as f:
                json.dump(self._corrections, f, indent=2, ensure_ascii=False)
            logger.info("LearningEngine: Saved %d corrections to %s", len(self._corrections), self._filepath)
        except Exception as e:
            logger.error("LearningEngine: Error saving corrections: %s", e)

    def is_correction(self, text: str) -> bool:
        """Check if the user input is a correction statement."""
        lower = text.lower().strip()
        return lower.startswith("no, i meant") or lower.startswith("no i meant") or lower.startswith("no, meant")

    def extract_correction_target(self, text: str) -> str:
        """Extract the corrected target from the correction statement."""
        lower = text.lower().strip()
        # Remove prefixes
        for prefix in ["no, i meant", "no i meant", "no, meant"]:
            if lower.startswith(prefix):
                return lower[len(prefix):].strip(" .?!,")
        return lower

    def learn(self, previous_query: str, correction_statement: str) -> Tuple[bool, str]:
        """
        Learn a new mapping from previous query to corrected target.
        
        Returns:
            (success, message)
        """
        if not previous_query:
            return False, "No previous query to correct."
        
        target = self.extract_correction_target(correction_statement)
        prev_clean = previous_query.lower().strip()
        
        if prev_clean in self._corrections:
            existing = self._corrections[prev_clean]
            if existing == target:
                return True, f"I already map '{previous_query}' to '{target}'."
            # Conflict detected: do not overwrite without confirmation
            return False, f"Conflict: '{previous_query}' is already mapped to '{existing}'. Overwrite requires confirmation."
            
        self._corrections[prev_clean] = target
        self._save()
        return True, f"Learned correction: '{previous_query}' -> '{target}'."

    def get_corrected_query(self, query: str) -> str:
        """Return the corrected query if we have learned it, otherwise the original query."""
        clean = query.lower().strip()
        if clean in self._corrections:
            corrected = self._corrections[clean]
            logger.info("LearningEngine: Mapping '%s' → '%s'", query, corrected)
            return corrected
        return query
