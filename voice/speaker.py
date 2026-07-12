"""
voice/speaker.py — Voice Reliability v3.0
==========================================
Module 4: speak() now returns the SpeechRequest object so callers can:
  - Block until complete via req.completed_event.wait()
  - Check req.status for SUCCESS / FAILED / CANCELLED / TIMEOUT
Module 9: lifecycle log line before delegating.
"""
from __future__ import annotations

import logging
from brain.speaking_engine.engine import AdaptiveSpeakingEngine, SpeechRequest, SpeechStatus

logger = logging.getLogger(__name__)

# Lazy global speaking engine init.
# Avoid import-time audio initialization (can behave differently in frozen EXEs).
_speaking_engine = None


def _get_speaking_engine():
    global _speaking_engine
    if _speaking_engine is not None:
        return _speaking_engine

    try:
        _speaking_engine = AdaptiveSpeakingEngine(use_pyttsx3=True)
    except Exception as e:
        logger.error("Failed to initialize AdaptiveSpeakingEngine: %s", e)
        # Provide a dummy fallback so it doesn't crash callers
        from brain.speaking_engine.engine import SpeechRequest

        class DummySpeakingEngine:
            def speak(self, *args, **kwargs):
                logger.warning("Speech suppressed due to engine failure.")
                return SpeechRequest("dummy", text="dummy", engine="dummy")

            def cancel(self):
                pass

        _speaking_engine = DummySpeakingEngine()

    return _speaking_engine
# Module 4: per-turn flag set by OllamaProvider when it streams speech directly
_has_spoken_in_turn: bool = False


def speak(
    text: str,
    profile: str = None,
    style: str = "Professional",
    cancel_previous: bool = True,
    block: bool = True,
) -> SpeechRequest:
    """
    Speak text aloud using the Adaptive Speaking Engine.
    Returns the SpeechRequest — callers can check .status and .completed_event.
    Default block=True ensures the call waits until audio finishes.
    """
    logger.info("[SPEECH REQUESTED] text='%s...'", text[:60])
    speaking_engine = _get_speaking_engine()
    req = speaking_engine.speak(

        text,
        profile=profile,
        style=style,
        cancel_previous=cancel_previous,
        block=block,
    )
    return req
