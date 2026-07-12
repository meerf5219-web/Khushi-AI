"""
ui/workers/memory_worker.py — Memory Worker
=============================================
Asynchronously executes memory operations (backup, restore, explicit statements) 
in a background QThread to ensure the UI remains fully responsive.
"""
from __future__ import annotations

import logging
from typing import Any
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class MemoryWorker(QThread):
    """
    Background worker for lifelong memory operations.
    """
    started = Signal()
    progress = Signal(int, str)
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, action: str, brain: Any, *args, **kwargs) -> None:
        super().__init__()
        self.action = action
        self.brain = brain
        self.args = args
        self.kwargs = kwargs

    def run(self) -> None:
        self.started.emit()
        try:
            self.progress.emit(10, "Starting memory operation...")
            if self.action == "backup":
                self.progress.emit(30, "Creating memory backup...")
                from memory.backup import BackupManager
                bm = BackupManager()
                password = self.kwargs.get("password", "")
                label = self.kwargs.get("label", "")
                result = bm.create_backup(password, label)
                self.progress.emit(100, "Backup created successfully.")
                self.finished.emit(result)
            elif self.action == "restore":
                self.progress.emit(30, "Restoring memory backup...")
                from memory.backup import BackupManager
                bm = BackupManager()
                password = self.kwargs.get("password", "")
                backup_name = self.kwargs.get("backup_name", "")
                result = bm.restore_backup(backup_name, password)
                self.progress.emit(100, "Memory restored successfully.")
                self.finished.emit(result)
            elif self.action == "save_statement":
                self.progress.emit(40, "Storing explicit statement...")
                text = self.kwargs.get("text", "")
                result = self.brain.memory.remember(text, category="personal")
                self.progress.emit(100, "Statement stored successfully.")
                self.finished.emit(result)
            else:
                raise ValueError(f"Unknown memory action: {self.action}")
        except Exception as e:
            logger.error(f"[MEMORY WORKER] Failure: {e}", exc_info=True)
            self.error.emit(str(e))
