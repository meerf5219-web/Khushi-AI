"""Notes skill for storing and retrieving simple text notes."""

from __future__ import annotations

import json
import logging
import os
from typing import List, Optional

from utils.paths import get_data_dir

logger = logging.getLogger(__name__)

NOTES_FILE = str(get_data_dir() / "memory" / "notes.json")


class NotesSkill:
    """Manage notes persisted in the assistant memory directory."""

    def create_note(self, text: str) -> Optional[str]:
        """Create a note from the provided text."""
        logger.info("NotesSkill create_note invoked")
        content = self._extract_note_content(text)
        if not content:
            return None

        notes = self._load_notes()
        notes.append(content)
        self._save_notes(notes)
        return f"Note saved: {content}"

    def show_notes(self) -> Optional[str]:
        """Return all saved notes as a single string."""
        logger.info("NotesSkill show_notes invoked")
        notes = self._load_notes()
        if not notes:
            return None

        return "\n".join(f"- {note}" for note in notes)

    def delete_notes(self) -> Optional[str]:
        """Delete all stored notes."""
        logger.info("NotesSkill delete_notes invoked")
        self._save_notes([])
        return "All notes deleted."

    def _extract_note_content(self, text: str) -> Optional[str]:
        """Extract note text from the input text."""
        cleaned = text.strip().lower()
        if not cleaned:
            return None

        for prefix in ["take note", "remember this note", "remember note"]:
            if cleaned.startswith(prefix):
                return text.replace(prefix, "", 1).strip()

        return None

    def _load_notes(self) -> List[str]:
        """Load notes from disk."""
        if not os.path.exists(NOTES_FILE):
            return []

        with open(NOTES_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
            if isinstance(data, list):
                return [str(item) for item in data]
        return []

    def _save_notes(self, notes: List[str]) -> None:
        """Persist notes to disk."""
        directory = os.path.dirname(NOTES_FILE)
        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(NOTES_FILE, "w", encoding="utf-8") as handle:
            json.dump(notes, handle, indent=4)
