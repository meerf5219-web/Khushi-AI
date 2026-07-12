"""
ui/workers/stream_worker.py — Generation 4 Event Stream Worker
==================================================================
Subscribes to the backend EventBus and bridges asynchronous backend events
into Qt QObject Signals. This ensures thread-safety when updating UI components.
"""
from __future__ import annotations

import logging
from PySide6.QtCore import QObject, Signal
from brain.event_bus import event_bus

logger = logging.getLogger(__name__)


class StreamWorker(QObject):
    """
    Bridge between python-level EventBus pub/sub and Qt6 signals.
    """
    token_received = Signal(str, str)         # Emits (new_token, full_text)
    speech_started = Signal(str)             # Emits request_id
    speech_completed = Signal(str, str)      # Emits (request_id, status_value)
    voice_interaction_received = Signal(str, str)  # Emits (user_text, assistant_response)

    def __init__(self) -> None:
        super().__init__()
        self._subscribe_all()

    def _subscribe_all(self) -> None:
        event_bus.subscribe("STREAM_TOKEN", self._on_stream_token)
        event_bus.subscribe("SPEECH_STARTED", self._on_speech_started)
        event_bus.subscribe("SPEECH_COMPLETED", self._on_speech_completed)
        event_bus.subscribe("VOICE_COMPANION_INTERACTION", self._on_voice_companion_interaction)
        logger.info("[STREAM WORKER] Registered subscribers with EventBus.")

    def _on_stream_token(self, data: dict) -> None:
        # Runs on event_bus thread; safely dispatch via Qt Signal
        token = data.get("token", "")
        full_text = data.get("full_text", "")
        self.token_received.emit(token, full_text)

    def _on_speech_started(self, data: dict) -> None:
        req_id = data.get("request_id", "")
        self.speech_started.emit(req_id)

    def _on_speech_completed(self, data: dict) -> None:
        req_id = data.get("request_id", "")
        status = data.get("status", "")
        self.speech_completed.emit(req_id, status)

    def _on_voice_companion_interaction(self, data: dict) -> None:
        user_text = data.get("user_text", "")
        assistant_response = data.get("assistant_response", "")
        self.voice_interaction_received.emit(user_text, assistant_response)
