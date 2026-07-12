"""File operations skill for creating, opening, deleting, and listing files."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class FileSkill:
    """Perform simple file-system operations using standard libraries."""

    def execute(self, text: str) -> Optional[str]:
        """Route a user request to the appropriate file operation."""
        logger.info("FileSkill executed with text: %s", text)
        normalized_text = text.lower().strip()

        if normalized_text.startswith("create folder"):
            name = normalized_text.replace("create folder", "", 1).strip()
            return self.create_folder(name)

        if normalized_text.startswith("create file"):
            name = normalized_text.replace("create file", "", 1).strip()
            return self.create_text_file(name)

        if normalized_text.startswith("open folder"):
            path = normalized_text.replace("open folder", "", 1).strip()
            return self.open_folder(path or ".")

        if normalized_text.startswith("delete file"):
            path = normalized_text.replace("delete file", "", 1).strip()
            return self.delete_file(path or ".")

        if normalized_text.startswith("list files"):
            path = normalized_text.replace("list files", "", 1).strip()
            return self.list_files(path or ".")

        return None

    def create_folder(self, name: str) -> str:
        """Create a folder at the given path or current directory."""
        if not name:
            return "Please provide a folder name."

        folder_path = Path(name).expanduser()
        try:
            folder_path.mkdir(parents=True, exist_ok=True)
            logger.info("Created folder: %s", folder_path)
            return f"Folder {folder_path.name} created."
        except OSError as exc:
            logger.exception("Failed to create folder: %s", exc)
            return f"I could not create the folder: {exc}"

    def create_text_file(self, name: str) -> str:
        """Create a text file with the provided name."""
        if not name:
            return "Please provide a file name."

        file_path = Path(name).expanduser()
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch(exist_ok=True)
            logger.info("Created file: %s", file_path)
            return f"{file_path.name} created."
        except OSError as exc:
            logger.exception("Failed to create file: %s", exc)
            return f"I could not create the file: {exc}"

    def open_folder(self, path: str) -> str:
        """Open a folder using the platform default handler."""
        target = Path(path).expanduser() if path else Path(".")
        try:
            if not target.exists():
                return f"Folder {target} not found."

            if hasattr(os, "startfile"):
                os.startfile(str(target))
            else:
                subprocess.Popen(["xdg-open", str(target)])

            logger.info("Opened folder: %s", target)
            return f"{target.name or str(target)} opened."
        except Exception as exc:
            logger.exception("Failed to open folder: %s", exc)
            return f"I could not open the folder: {exc}"

    def delete_file(self, path: str) -> str:
        """Delete the given file path if it exists."""
        if not path:
            return "Please provide a file path."

        target = Path(path).expanduser()
        try:
            if not target.exists():
                return f"File {target} not found."
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            logger.info("Deleted path: %s", target)
            return f"Deleted {target.name}."
        except OSError as exc:
            logger.exception("Failed to delete path: %s", exc)
            return f"I could not delete the file: {exc}"

    def list_files(self, path: str) -> str:
        """List files and folders in the requested path."""
        target = Path(path).expanduser() if path else Path(".")
        try:
            if not target.exists():
                return f"Folder {target} not found."

            entries = sorted(entry.name for entry in target.iterdir())
            if not entries:
                return f"No files found in {target.name or str(target)}."

            logger.info("Listed files in: %s", target)
            return f"Files in {target.name or str(target)}: {', '.join(entries)}"
        except OSError as exc:
            logger.exception("Failed to list files: %s", exc)
            return f"I could not list the files: {exc}"
