"""
ui/widgets/conversation/export_manager.py — Conversation Export Engine
=======================================================================
Formats and exports the current conversation history logs into TXT, Markdown,
and JSON files.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List
from version import APP_NAME

logger = logging.getLogger(__name__)


class ExportManager:
    """
    Handles formatting and writing conversation history streams into clean files.
    """

    @staticmethod
    def to_txt(turns: List[Dict[str, Any]], file_path: str) -> bool:
        """Export dialogues to a readable plain text file."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("=========================================\n")
                f.write(f"       {APP_NAME} Conversation Export     \n")
                f.write("=========================================\n\n")
                for turn in turns:
                    speaker = "USER" if turn["source"] == "user" else "ASSISTANT"
                    f.write(f"[{speaker}]:\n{turn['raw_text']}\n")
                    f.write("-" * 40 + "\n\n")
            logger.info("[EXPORT MANAGER] Exported TXT file successfully: %s", file_path)
            return True
        except Exception as exc:
            logger.error("[EXPORT MANAGER] Failed to export TXT: %s", exc)
            return False

    @staticmethod
    def to_markdown(turns: List[Dict[str, Any]], file_path: str) -> bool:
        """Export dialogues preserving Markdown structures."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# {APP_NAME} Conversation Logs\n\n")
                for turn in turns:
                    speaker = "**User**" if turn["source"] == "user" else f"**{APP_NAME}**"
                    f.write(f"### {speaker}\n\n{turn['raw_text']}\n\n---\n\n")
            logger.info("[EXPORT MANAGER] Exported MD file successfully: %s", file_path)
            return True
        except Exception as exc:
            logger.error("[EXPORT MANAGER] Failed to export MD: %s", exc)
            return False

    @staticmethod
    def to_json(turns: List[Dict[str, Any]], file_path: str) -> bool:
        """Export the full dialogue tree structure with metadata metrics as JSON."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(turns, f, indent=2, ensure_ascii=False)
            logger.info("[EXPORT MANAGER] Exported JSON file successfully: %s", file_path)
            return True
        except Exception as exc:
            logger.error("[EXPORT MANAGER] Failed to export JSON: %s", exc)
            return False
