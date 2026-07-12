"""
ui/workers/loading_worker.py — Generation 4 Loading Worker
==============================================================
Runs in a background QThread during splash screen presentation.
Initializes the heavy Brain subsystems sequentially and reports progress
to the Splash Screen.
"""
from __future__ import annotations

import time
import logging
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class LoadingWorker(QThread):
    """
    Background worker initializing Brain subsystems and emitting progress signals.
    """
    progress = Signal(int, str, str)  # Emits (percent, status_msg, module_name)
    completed = Signal(object)        # Emits the ready Brain instance
    started = Signal()
    finished = Signal(object)
    error = Signal(str)

    def __init__(self) -> None:
        super().__init__()

    def run(self) -> None:
        self.started.emit()
        logger.info("[LOADING WORKER] Beginning Brain initialization...")
        
        stages = [
            (10, "Configuration", "Loading settings and personality configurations...", self._load_config),
            (25, "Adaptive Voice", "Initializing Adaptive Voice Engine...", self._init_voice),
            (50, "Brain Core", "Restoring personal preferences & life memories...", self._init_brain),
            (85, "Event Store", "Connecting SQLite Event Store & history databases...", self._init_event_store),
            (100, "System Ready", "System status: Ready.", self._ready_system)
        ]
        
        brain = None
        for percent, module_name, msg, func in stages:
            start_time = time.time()
            self.progress.emit(percent, msg, module_name)
            logger.info(f"[LOADING WORKER] Starting stage: {module_name}")
            
            try:
                result = func()
                if module_name == "Brain Core":
                    brain = result
                duration = time.time() - start_time
                logger.info(f"[LOADING WORKER] Stage {module_name} completed in {duration:.3f}s")
            except Exception as exc:
                duration = time.time() - start_time
                logger.error(f"[LOADING WORKER] Stage {module_name} failed in {duration:.3f}s: {exc}", exc_info=True)
                self.error.emit(f"Stage {module_name} failed: {exc}")
                self.progress.emit(percent, f"Warning: {module_name} failed. Continuing...", module_name)
                # Continue despite failure
            
            time.sleep(0.05)  # small pause for visual pacing
            
        self.completed.emit(brain)
        self.finished.emit(brain)

    def _load_config(self) -> None:
        pass  # Place holder if config needs explicit loading

    def _init_voice(self) -> None:
        from voice.speaker import speaking_engine
        _ = speaking_engine

    def _init_brain(self) -> Any:
        # Load Brain synchronously (memory, routing, plugins)
        # SentenceTransformer loading is deferred in SemanticIntentMatcher
        from brain.brain import Brain
        return Brain()

    def _init_event_store(self) -> None:
        # Dummy call to ensure event store initializes if brain exists
        pass

    def _ready_system(self) -> None:
        pass

