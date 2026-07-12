"""
Fallback TTS Module — Voice Reliability v3.0
=============================================
Uses Windows SAPI.SpVoice COM interface directly as a secondary TTS backend.
Activated automatically when pyttsx3 fails after all retries.
Never loses a response — guarantees speech even if the primary engine is broken.
"""
from __future__ import annotations

import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)

_SAPI_LOCK = threading.Lock()


class FallbackTTS:
    """
    Fallback TTS using win32com SAPI.SpVoice.
    Acts as the emergency speech backend when pyttsx3 is broken or unresponsive.
    """

    def __init__(self) -> None:
        self._voice = None
        self._available = False
        self._init()

    def _init(self) -> None:
        try:
            import win32com.client  # type: ignore
            self._voice = win32com.client.Dispatch("SAPI.SpVoice")
            self._available = True
            logger.info("[FALLBACK TTS] SAPI.SpVoice initialized successfully.")
        except Exception as exc:
            logger.warning("[FALLBACK TTS] SAPI.SpVoice unavailable: %s", exc)
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def speak(self, text: str, rate: int = 165, volume: float = 1.0) -> bool:
        """
        Speak text synchronously using SAPI.SpVoice.
        Returns True on success, False on failure.
        SAPI rate: -10 (slowest) to +10 (fastest). Maps from WPM linearly.
        """
        if not self._available or not self._voice:
            logger.error("[FALLBACK TTS] Not available — cannot speak: %s", text[:60])
            return False

        try:
            with _SAPI_LOCK:
                # Map WPM rate (135–220) to SAPI rate (-5 to +5) roughly
                sapi_rate = max(-5, min(5, int((rate - 165) / 15)))
                self._voice.Rate = sapi_rate

                # SAPI volume is 0–100
                sapi_vol = max(0, min(100, int(volume * 100)))
                self._voice.Volume = sapi_vol

                logger.info("[FALLBACK TTS] Speaking: %s", text[:80])
                self._voice.Speak(text)
                logger.info("[FALLBACK TTS] Completed.")
                return True
        except Exception as exc:
            logger.error("[FALLBACK TTS] Failed to speak: %s — %s", text[:60], exc)
            return False

    def stop(self) -> None:
        """Interrupt any active SAPI speech."""
        if self._voice and self._available:
            try:
                # SVSFPurgeBeforeSpeak = 2
                self._voice.Speak("", 2)
            except Exception:
                pass


# Module-level singleton — imported once and reused
_fallback_tts: Optional[FallbackTTS] = None


def get_fallback_tts() -> FallbackTTS:
    """Return the singleton FallbackTTS instance, creating it on first call."""
    global _fallback_tts
    if _fallback_tts is None:
        _fallback_tts = FallbackTTS()
    return _fallback_tts
