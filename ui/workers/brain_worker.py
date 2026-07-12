"""
ui/workers/brain_worker.py — Generation 4 Brain Worker
============================================================
Runs brain.think(text) in a background thread to keep the main GUI 60 FPS
responsive. Emits latency metrics and response content.
"""
from __future__ import annotations

import time
import logging
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class BrainWorker(QThread):
    """
    QThread wrapper for non-blocking Brain inference processing.
    """
    finished = Signal(str, float)  # Emits (response_text, elapsed_seconds)
    failed = Signal(str)            # Emits error message
    started = Signal()
    progress = Signal(int, str)
    error = Signal(str)

    def __init__(self, brain: Any, text: str) -> None:
        super().__init__()
        self.brain = brain
        self.text = text

    def run(self) -> None:
        self.started.emit()
        try:
            logger.info("[BRAIN WORKER] Processing query: '%s'", self.text[:60])
            self.progress.emit(10, "Initializing query processing...")
            t0 = time.perf_counter()
            
            # Execute the conversational pipeline
            self.progress.emit(50, "Reasoning & generating reply...")
            reply = self.brain.think(self.text)
            
            elapsed = time.perf_counter() - t0
            logger.info("[BRAIN WORKER] Completed processing in %.3fs", elapsed)
            
            self.progress.emit(100, "Processing completed.")
            self.finished.emit(reply, elapsed)
        except Exception as exc:
            logger.exception("[BRAIN WORKER] Error during think processing: %s", exc)
            self.error.emit(str(exc))
            self.failed.emit(str(exc))
