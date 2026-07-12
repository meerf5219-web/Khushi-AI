"""
voice/voice_engine.py — Voice Engine v2
=========================================
Fix: Issue 1 — pyttsx3 "run loop already started"
Root cause: pyttsx3's COM event loop (runAndWait) is not re-entrant.
If called from multiple threads or before the previous call completes,
it raises "run loop already started".

Solution:
  - Module-level pyttsx3 singleton: only ONE engine instance for the process.
  - Module-level threading.Lock: serializes all say() + runAndWait() calls.
  - No concurrent runAndWait() is ever possible.
  - Initialization is guarded by a separate init-lock to prevent duplicate init.
"""
from __future__ import annotations

import os
import re
import time
import uuid
import wave
import struct
import logging
import tempfile
import threading
from typing import Dict, List, Optional, Any, Callable

logger = logging.getLogger(__name__)

try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False

# ---------------------------------------------------------------------------
# Issue 1: Module-level pyttsx3 singleton + serialization lock
# ---------------------------------------------------------------------------
_pyttsx3_engine: Any = None
_pyttsx3_lock = threading.Lock()          # serializes say() + runAndWait()
_pyttsx3_init_lock = threading.Lock()    # guards one-time initialization
_pyttsx3_available = False


def _get_pyttsx3_engine() -> Any:
    """
    Return the module-level pyttsx3 engine singleton.
    Initializes on first call; subsequent calls return the cached instance.
    Thread-safe via double-checked locking.
    """
    global _pyttsx3_engine, _pyttsx3_available
    if _pyttsx3_engine is not None:
        return _pyttsx3_engine

    with _pyttsx3_init_lock:
        if _pyttsx3_engine is not None:          # re-check after acquiring lock
            return _pyttsx3_engine
        try:
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            if voices:
                engine.setProperty("voice", voices[0].id)
            _pyttsx3_engine = engine
            _pyttsx3_available = True
            logger.info("VoiceEngineV2: pyttsx3 singleton initialized.")
        except Exception as exc:
            logger.warning("VoiceEngineV2: pyttsx3 initialization failed: %s", exc)
            _pyttsx3_available = False
    return _pyttsx3_engine


class VoiceEngineV2:
    """
    Voice Engine v2 (Phase 7.8 + Issue-1 Fix)
    ------------------------------------------
    Uses a module-level pyttsx3 singleton protected by a threading.Lock
    so runAndWait() is never called concurrently from multiple threads.
    """

    def __init__(self, use_pyttsx3: bool = True, default_voice_index: int = 0):
        self.use_pyttsx3 = use_pyttsx3
        self.use_file_playback = False  # Force false to prevent pyttsx3 save_to_file deadlock

        if self.use_pyttsx3:
            engine = _get_pyttsx3_engine()
            if engine is None:
                self.use_pyttsx3 = False
                logger.warning("VoiceEngineV2: running in dummy mode (pyttsx3 unavailable).")

        # Expose .engine and .voices for backward compatibility
        self.engine = _pyttsx3_engine if self.use_pyttsx3 else None
        self.voices = self.engine.getProperty("voices") if self.engine else []
        self.current_voice_id = self.voices[default_voice_index].id if self.voices else None

        # Pronunciation Dictionary
        self.pronunciation_dict: Dict[str, str] = {
            r"\bUPSC\b": "U P S C",
            r"\bJKPSC\b": "J K P S C",
            r"\bOBD-II\b": "O B D 2",
            r"\bPython\b": "Python",
            r"\bGitHub\b": "Git Hub",
            r"\bRAG\b": "R A G",
            r"\bFAISS\b": "Fase",
            r"\bChromaDB\b": "Chroma D B",
        }

        self.performance_logs: List[Dict[str, Any]] = []

    def set_voice(self, voice_id_or_index: Any) -> None:
        """Switch voice by ID, name substring, or index."""
        if not self.use_pyttsx3 or not self.engine:
            return
        try:
            if isinstance(voice_id_or_index, int):
                if 0 <= voice_id_or_index < len(self.voices):
                    self.current_voice_id = self.voices[voice_id_or_index].id
                    self.engine.setProperty("voice", self.current_voice_id)
                    logger.info(
                        "VoiceEngineV2: Switched to voice index %d (%s)",
                        voice_id_or_index,
                        self.voices[voice_id_or_index].name,
                    )
            elif isinstance(voice_id_or_index, str):
                for v in self.voices:
                    if voice_id_or_index == v.id or voice_id_or_index.lower() in v.name.lower():
                        self.current_voice_id = v.id
                        self.engine.setProperty("voice", v.id)
                        logger.info("VoiceEngineV2: Switched to voice %s", v.name)
                        break
        except Exception as exc:
            logger.error("VoiceEngineV2: Failed to set voice: %s", exc)

    def get_voices(self) -> List[Dict[str, Any]]:
        """Get all available voices."""
        return [{"id": v.id, "name": v.name, "languages": v.languages} for v in self.voices]

    def add_custom_pronunciation(self, word: str, pronunciation: str) -> None:
        """Allow adding custom pronunciation rules dynamically."""
        pattern = rf"\b{re.escape(word)}\b"
        self.pronunciation_dict[pattern] = pronunciation
        logger.info("VoiceEngineV2: Added custom pronunciation: %s -> %s", word, pronunciation)

    def apply_pronunciation(self, text: str) -> str:
        """Apply pronunciation dictionary using regex word-boundary replacements."""
        cleaned_text = text
        for pattern, replacement in self.pronunciation_dict.items():
            cleaned_text = re.sub(pattern, replacement, cleaned_text, flags=re.IGNORECASE)
        return cleaned_text

    def apply_breathing(self, text: str) -> str:
        """Inject small natural pauses into long text blocks."""
        words = text.split()
        if len(words) < 10:
            return text
        text = re.sub(r"\b(but|because|although)\b", r", \1", text)
        text = re.sub(r",\s*,", ",", text)
        return text

    def apply_prosody(self, text: str, is_question: bool) -> str:
        """Adjust sentence structure for prosody."""
        if is_question and not text.endswith("?"):
            return text + "?"
        return text

    def _normalize_wav(self, file_path: str) -> None:
        """Peak normalize WAV volume and apply 10ms fade-in/fade-out."""
        try:
            with wave.open(file_path, "rb") as wav_in:
                params = wav_in.getparams()
                nchannels, sampwidth, framerate, nframes, comptype, compname = params
                if sampwidth != 2:
                    return
                frames = wav_in.readframes(nframes)
            num_samples = len(frames) // 2
            samples = list(struct.unpack(f"<{num_samples}h", frames))
            if not samples:
                return
            max_val = max(abs(s) for s in samples)
            if max_val == 0:
                return
            target_peak = 29491
            scale = target_peak / max_val
            fade_len = min(int(framerate * 0.01), num_samples // 2)
            for i in range(num_samples):
                val = float(samples[i]) * scale
                if i < fade_len:
                    val *= i / fade_len
                elif i > num_samples - fade_len:
                    val *= (num_samples - i) / fade_len
                val = max(-32768, min(32767, val))
                samples[i] = int(val)
            new_frames = struct.pack(f"<{num_samples}h", *samples)
            with wave.open(file_path, "wb") as wav_out:
                wav_out.setparams(params)
                wav_out.writeframes(new_frames)
        except Exception as exc:
            logger.error("VoiceEngineV2: WAV normalization failed: %s", exc)

    def speak_action(
        self,
        text: str,
        rate: int,
        volume: float,
        profile: str,
        style: str,
        sleep_multiplier: float = 1.0,
        stop_check_func: Optional[Callable[[], bool]] = None,
    ) -> Dict[str, Any]:
        """
        Process and speak a single text action.
        Issue 1 Fix: acquires _pyttsx3_lock before say()/runAndWait()
        so only ONE thread can drive the pyttsx3 event loop at a time.
        """
        t_submit = time.perf_counter()

        # Apply text processing
        processed_text = self.apply_pronunciation(text)
        processed_text = self.apply_breathing(processed_text)
        is_question = text.strip().endswith("?")
        processed_text = self.apply_prosody(processed_text, is_question)

        actual_rate = rate
        actual_volume = min(1.0, max(0.0, volume))

        # Profile-specific voice configurations (set_voice uses property access only,
        # which is safe without the full lock)
        if profile == "Friendly":
            self.set_voice("zira")
            actual_rate = int(rate * 1.05)
        elif profile == "Professional":
            self.set_voice("david")
        elif profile == "Teaching":
            actual_rate = int(rate * 0.85)
        elif profile == "Technical":
            actual_rate = int(rate * 0.95)

        t_gen_start = time.perf_counter()
        generation_time = 0.0
        playback_latency = 0.0

        if self.use_pyttsx3 and self.engine:
            # Issue 1: Acquire the global lock so no other thread can call
            # runAndWait() concurrently — prevents "run loop already started".
            with _pyttsx3_lock:
                # Check interruption before entering pyttsx3 loop
                if stop_check_func and stop_check_func():
                    logger.info("VoiceEngineV2: stop requested before speak_action, skipping.")
                    generation_time = time.perf_counter() - t_gen_start
                    playback_latency = 0.0
                else:
                    try:
                        self.engine.setProperty("rate", actual_rate)
                        self.engine.setProperty("volume", actual_volume)
                        playback_latency = time.perf_counter() - t_submit
                        self.engine.say(processed_text)
                        self.engine.runAndWait()
                        generation_time = time.perf_counter() - t_gen_start
                    except Exception as exc:
                        logger.warning(
                            "VoiceEngineV2: pyttsx3 execution failed — re-raising for retry engine: %s",
                            exc,
                        )
                        # Re-raise so AdaptiveSpeakingEngine retry/fallback handles it
                        raise
        else:
            # Dummy mode — deterministic sleep for test environments
            words = len(processed_text.split())
            speak_time = (words / actual_rate) * 60.0
            playback_latency = 0.001
            generation_time = time.perf_counter() - t_gen_start
            time.sleep(max(0.01, speak_time * sleep_multiplier))

        total_time = time.perf_counter() - t_submit
        metrics = {
            "text": text,
            "processed_text": processed_text,
            "profile": profile,
            "style": style,
            "generation_time": generation_time,
            "playback_latency": playback_latency,
            "total_time": total_time,
        }
        self.performance_logs.append(metrics)
        return metrics
