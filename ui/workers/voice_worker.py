"""
ui/workers/voice_worker.py — Generation 4 Voice Worker
==========================================================
Runs the Speech-to-Text (listen) engine on a background QThread.
Uses short timeouts on SpeechRecognition to remain responsive to pause/resume
and stop signals from the main GUI thread.
"""
from __future__ import annotations

import time
import logging
import speech_recognition as sr
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class VoiceWorker(QThread):
    """
    Background worker capturing voice input and forwarding recognized text.
    """
    text_detected = Signal(str)       # Emits transcribed text
    status_changed = Signal(str)      # Emits status (Listening, Offline, etc)
    audio_amplitude = Signal(float)   # Emits voice level for waveform visualization
    started = Signal()
    progress = Signal(int, str)
    finished = Signal()
    error = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._running = True
        self._enabled = True
        
        # Initialize SpeechRecognition objects
        self.recognizer = sr.Recognizer()
        self.microphone = None
        
        try:
            self.microphone = sr.Microphone()
            logger.info("[VOICE WORKER] Microphone initialized successfully.")
        except Exception as exc:
            logger.error("[VOICE WORKER] Microphone initialization failed: %s", exc)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable voice processing (e.g. paused while speaking)."""
        self._enabled = enabled
        logger.info("[VOICE WORKER] Enabled state set to: %s", enabled)
        if enabled:
            self.status_changed.emit("Listening")
        else:
            self.status_changed.emit("Offline")

    def stop(self) -> None:
        """Request thread shutdown."""
        self._running = False
        self.wait()

    def run(self) -> None:
        self.started.emit()
        if not self.microphone:
            self.status_changed.emit("Offline")
            logger.error("[VOICE WORKER] No microphone available — thread exiting.")
            self.error.emit("No microphone available")
            self.finished.emit()
            return

        logger.info("[VOICE WORKER] Speech loop started.")
        self.status_changed.emit("Listening")

        # Adjust for ambient noise once on start
        try:
            self.progress.emit(20, "Adjusting for ambient noise...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
            self.progress.emit(100, "Calibration completed.")
        except Exception as exc:
            logger.warning("[VOICE WORKER] Ambient noise adjustment failed: %s", exc)
            self.error.emit(f"Ambient noise adjustment failed: {exc}")

        while self._running:
            if not self._enabled:
                time.sleep(0.2)
                continue

            try:
                with self.microphone as source:
                    # Use a short timeout so we check self._running and self._enabled frequently
                    audio = self.recognizer.listen(source, timeout=1.0, phrase_time_limit=12.0)
                
                # Double-check state before processing
                if not self._running or not self._enabled:
                    continue

                self.status_changed.emit("Thinking")
                self.progress.emit(50, "Recognizing speech...")
                text = self.recognizer.recognize_google(audio)
                self.progress.emit(100, "Speech recognized.")
                
                if text.strip():
                    logger.info("[VOICE WORKER] Recognized: '%s'", text)
                    self.text_detected.emit(text.lower())
                else:
                    self.status_changed.emit("Listening")
                    
            except sr.WaitTimeoutError:
                # Normal path when no speech is detected within the 1-second timeout
                # Emit small noise variations for the passive waveform effect
                self.audio_amplitude.emit(0.02)
            except (sr.UnknownValueError, sr.RequestError) as exc:
                # Google Speech Recognition couldn't understand or connection issue
                self.status_changed.emit("Listening")
            except Exception as exc:
                logger.error("[VOICE WORKER] Loop exception: %s", exc)
                self.error.emit(f"Loop exception: {exc}")
                self.status_changed.emit("Listening")
                time.sleep(0.5)

        self.status_changed.emit("Offline")
        logger.info("[VOICE WORKER] Speech loop exited.")
        self.finished.emit()
