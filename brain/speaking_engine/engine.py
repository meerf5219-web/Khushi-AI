"""
Adaptive Speaking Engine — Voice Reliability v3.0
==================================================
Modules implemented:
  1  Speech Confirmation  — SpeechStatus enum on every request
  2  Retry Engine         — 3 attempts, exponential backoff
  3  Speech Watchdog      — per-utterance timeout thread
  5  Queue Integrity      — deduplication, CANCELLED status on drain
  8  Health Monitor       — counters, avg latency, report every 10 requests
  9  Logging              — standardized lifecycle log lines
"""
from __future__ import annotations

import enum
import logging
import queue
import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, List, Optional, Union

logger = logging.getLogger(__name__)

# Speak rates (Words Per Minute)
RATE_FAST = 200
RATE_MODERATE = 165
RATE_SLOW = 135

# Reliability configuration
MAX_RETRIES: int = 3
RETRY_BASE_DELAY: float = 0.2   # seconds (doubled each attempt)
SPEECH_TIMEOUT: float = 30.0    # seconds per utterance watchdog
DEDUP_WINDOW: float = 0.1       # seconds — ignore identical text within this window


class SpeechStatus(enum.Enum):
    """Lifecycle status of a single SpeechRequest."""
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    INTERRUPTED = "INTERRUPTED"
    TIMEOUT = "TIMEOUT"


@dataclass
class SpeechAction:
    action_type: str  # "speak" or "pause"
    text: str = ""
    rate: int = RATE_MODERATE
    volume: float = 1.0
    style: str = "Professional"
    profile: str = "General Chat"
    emphasis: bool = False
    duration: float = 0.0


@dataclass
class SpeechRequest:
    request_id: str
    submit_time: float
    chunks_generator: Optional[Generator[str, None, None]] = None
    static_text: Optional[str] = None
    profile: Optional[str] = None
    style: str = "Professional"
    cancel_previous: bool = True
    priority: int = 1
    # Tracking latencies
    queue_time: float = 0.0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    speech_latency: float = 0.0
    total_response_latency: float = 0.0
    # Module 1: status
    status: SpeechStatus = field(default=SpeechStatus.PENDING)
    completed_event: threading.Event = field(default_factory=threading.Event)


@dataclass
class HealthMonitor:
    """Module 8: tracks aggregate voice engine statistics."""
    total_requests: int = 0
    success_count: int = 0
    fail_count: int = 0
    retry_count: int = 0
    interrupt_count: int = 0
    timeout_count: int = 0
    cancelled_count: int = 0
    _latency_sum: float = 0.0
    _latency_count: int = 0

    def record(self, status: SpeechStatus, latency: float = 0.0) -> None:
        self.total_requests += 1
        if status == SpeechStatus.SUCCESS:
            self.success_count += 1
            self._latency_sum += latency
            self._latency_count += 1
        elif status == SpeechStatus.FAILED:
            self.fail_count += 1
        elif status in (SpeechStatus.CANCELLED, SpeechStatus.INTERRUPTED):
            self.interrupt_count += 1
            self.cancelled_count += 1
        elif status == SpeechStatus.TIMEOUT:
            self.timeout_count += 1

    def record_retry(self) -> None:
        self.retry_count += 1

    @property
    def avg_latency(self) -> float:
        if self._latency_count == 0:
            return 0.0
        return self._latency_sum / self._latency_count

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.success_count / self.total_requests

    def get_report(self) -> str:
        return (
            f"[HEALTH] requests={self.total_requests} "
            f"success={self.success_count} "
            f"fail={self.fail_count} "
            f"retries={self.retry_count} "
            f"interrupts={self.interrupt_count} "
            f"timeouts={self.timeout_count} "
            f"success_rate={self.success_rate:.1%} "
            f"avg_latency={self.avg_latency:.3f}s"
        )


class AdaptiveSpeakingEngine:
    """
    Adaptive Speaking Engine (Voice Reliability v3.0)
    --------------------------------------------------
    Sits between Response Composer and the Speaker/TTS Engine.
    Adjusts pacing, inserts natural pauses, emphasizes key terms,
    supports streaming speech, queue management, and interruption handling.
    Now includes: status tracking, retries, watchdog, fallback TTS,
    health monitoring, and standardized lifecycle logging.
    """
    def __init__(self, use_pyttsx3: bool = True, sleep_multiplier: float = 1.0):
        self.use_pyttsx3 = use_pyttsx3
        self.sleep_multiplier = sleep_multiplier

        self.voice_engine = None
        self.engine = None
        self.voices = []

        self.queue: queue.PriorityQueue = queue.PriorityQueue()
        self.current_request: Optional[SpeechRequest] = None
        self.is_paused = False
        self.is_playing = False

        # Thread synchronization
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set()  # Unpaused initially

        # Module 8: Health Monitor
        self.health = HealthMonitor()

        # History & performance logs
        self.performance_logs: List[Dict[str, Any]] = []
        self.spoken_actions_log: List[SpeechAction] = []  # For test verifications

        # Module 5: deduplication — track (text, submit_time) of last enqueued item
        self._last_queued_text: str = ""
        self._last_queued_time: float = 0.0

        # Start background worker thread
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def speak(
        self,
        text: str,
        profile: Optional[str] = None,
        style: str = "Professional",
        cancel_previous: bool = True,
        block: bool = False,
    ) -> SpeechRequest:
        """Speak a static block of text. Returns the SpeechRequest for status checking."""
        logger.info("[SPEECH REQUESTED] text='%s...'", text[:60])
        request_id = str(uuid.uuid4())
        req = SpeechRequest(
            request_id=request_id,
            submit_time=time.perf_counter(),
            static_text=text,
            profile=profile,
            style=style,
            cancel_previous=cancel_previous,
        )
        self._submit_request(req)
        if block:
            req.completed_event.wait()
        return req

    def speak_stream(
        self,
        generator: Generator[str, None, None],
        profile: Optional[str] = None,
        style: str = "Professional",
        cancel_previous: bool = True,
        block: bool = False,
    ) -> SpeechRequest:
        """Speak a stream of text chunks. Returns the SpeechRequest for status checking."""
        logger.info("[SPEECH REQUESTED] streaming generator")
        request_id = str(uuid.uuid4())
        req = SpeechRequest(
            request_id=request_id,
            submit_time=time.perf_counter(),
            chunks_generator=generator,
            profile=profile,
            style=style,
            cancel_previous=cancel_previous,
        )
        self._submit_request(req)
        if block:
            req.completed_event.wait()
        return req

    def stop(self) -> None:
        """Stop current speech immediately."""
        logger.info("SpeakingEngine: stop() requested.")
        self.stop_event.set()
        self.pause_event.set()  # Wake up if paused
        if self.current_request:
            self.current_request.status = SpeechStatus.INTERRUPTED
            self.current_request.completed_event.set()
            self.health.interrupt_count += 1

    def pause(self) -> None:
        """Pause speech playback."""
        logger.info("SpeakingEngine: pause() requested.")
        self.is_paused = True
        self.pause_event.clear()

    def resume(self) -> None:
        """Resume speech playback."""
        logger.info("SpeakingEngine: resume() requested.")
        self.is_paused = False
        self.pause_event.set()

    def cancel(self) -> None:
        """Cancel all queued and active speeches."""
        logger.info("SpeakingEngine: cancel() requested.")
        self.stop()
        # Drain queue — Module 5: set CANCELLED status on each
        while not self.queue.empty():
            try:
                _, _, req = self.queue.get_nowait()
                req.status = SpeechStatus.CANCELLED
                req.completed_event.set()
                self.health.cancelled_count += 1
            except queue.Empty:
                break

    def get_performance_logs(self) -> List[Dict[str, Any]]:
        """Return the captured performance logs."""
        return self.performance_logs

    def get_health_report(self) -> str:
        """Return the current health statistics as a formatted string."""
        return self.health.get_report()

    # ------------------------------------------------------------------
    # Profile / Pacing helpers (unchanged)
    # ------------------------------------------------------------------

    def detect_profile(self, text: str) -> str:
        """Auto-detect speaking profile based on text content."""
        lower = text.lower()
        if "```" in lower or ".py" in lower or "def " in lower or "class " in lower:
            return "Coding"
        if any(w in lower for w in ["warning", "caution", "danger", "critical"]):
            return "Warnings"
        if any(w in lower for w in ["error", "failed to", "invalid", "exception"]):
            return "Error Messages"
        if any(w in lower for w in ["success", "completed", "done", "passed", "congratulations"]):
            return "Success Messages"
        if any(w in lower for w in ["explain", "tutorial", "learn", "how to", "understand", "concept"]):
            return "Teaching"
        if any(w in lower for w in ["keep going", "proud of you", "believe in", "encourage", "you can do it"]):
            return "Motivation"
        return "General Chat"

    def calculate_pacing(self, text: str, profile: str) -> int:
        """Calculate pacing rate in WPM based on text length and profile."""
        if profile == "Warnings":
            base_rate = RATE_SLOW - 10
        elif profile == "Motivation":
            base_rate = RATE_SLOW
        elif profile == "Error Messages":
            base_rate = RATE_FAST - 10
        elif profile == "Success Messages":
            base_rate = RATE_FAST
        elif profile == "Teaching":
            base_rate = RATE_MODERATE - 15
        elif profile == "Coding":
            base_rate = RATE_SLOW + 10
        else:
            base_rate = RATE_MODERATE

        char_len = len(text)
        if char_len < 60:
            base_rate = min(220, base_rate + 25)
        elif char_len > 200:
            base_rate = max(145, base_rate - 10)

        return base_rate

    def parse_actions(self, text: str, profile: str, style_name: str) -> List[SpeechAction]:
        """Parse text into a list of SpeechActions (speak chunks and pauses)."""
        actions: List[SpeechAction] = []
        volume = 1.0
        if style_name == "Calm":
            volume = 0.8
        elif style_name == "Confident":
            volume = 1.0

        paragraphs = text.split("\n\n")
        for idx_p, para in enumerate(paragraphs):
            para = para.strip()
            if not para:
                continue
            lines = para.split("\n")
            is_list = len(lines) > 1 and any(
                re.match(r"^(\s*[-*•]|\s*\d+\.)", line) for line in lines
            )
            if is_list:
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    clean_line = re.sub(r"^([-*•]|\d+\.)\s*", "", line)
                    self._parse_segment_actions(clean_line, profile, style_name, volume, actions)
                    actions.append(SpeechAction(action_type="pause", duration=0.4, profile=profile))
            else:
                self._parse_segment_actions(para, profile, style_name, volume, actions)
            if idx_p < len(paragraphs) - 1:
                actions.append(SpeechAction(action_type="pause", duration=0.6, profile=profile))
        return actions

    def _parse_segment_actions(
        self,
        segment_text: str,
        profile: str,
        style_name: str,
        volume: float,
        actions: List[SpeechAction],
    ) -> None:
        sentences = re.split(r"([.!?]+)", segment_text)
        for idx in range(0, len(sentences) - 1, 2):
            sentence = sentences[idx].strip()
            punct = sentences[idx + 1].strip() if (idx + 1) < len(sentences) else ""
            if not sentence:
                continue
            pause_dur = 0.25
            if "?" in punct:
                pause_dur = 0.3
            clauses = re.split(r"([;:]|--|\s-\s)", sentence)
            for c_idx in range(len(clauses)):
                clause = clauses[c_idx].strip()
                if not clause:
                    continue
                if clause in [";", ":", "--", "-", "- "]:
                    actions.append(SpeechAction(action_type="pause", duration=0.2, profile=profile))
                    continue
                self._apply_emphasis(clause, profile, style_name, volume, actions)
            actions.append(SpeechAction(action_type="pause", duration=pause_dur, profile=profile))
        if len(sentences) % 2 != 0:
            trail = sentences[-1].strip()
            if trail:
                self._apply_emphasis(trail, profile, style_name, volume, actions)

    def _apply_emphasis(
        self,
        text: str,
        profile: str,
        style_name: str,
        volume: float,
        actions: List[SpeechAction],
    ) -> None:
        patterns = [
            r"\b(warning|caution|danger|critical|important|stop)\b",
            r"\b(due by|deadline|by tomorrow|due date|expiry)\b",
            r"\b(\d+%\b|\b\d{2,}\b)",
            r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}\b",
            r"\b(\d{4}-\d{2}-\d{2})\b",
            r"\b(goal|target|milestone|upsc)\b",
        ]
        combined_pattern = re.compile("|".join(patterns), re.IGNORECASE)
        matches = list(combined_pattern.finditer(text))
        base_rate = self.calculate_pacing(text, profile)
        if not matches:
            actions.append(
                SpeechAction(
                    action_type="speak",
                    text=text,
                    rate=base_rate,
                    volume=volume,
                    style=style_name,
                    profile=profile,
                )
            )
            return
        last_idx = 0
        for m in matches:
            start, end = m.span()
            if start > last_idx:
                norm_text = text[last_idx:start].strip()
                if norm_text:
                    actions.append(
                        SpeechAction(
                            action_type="speak",
                            text=norm_text,
                            rate=base_rate,
                            volume=volume,
                            style=style_name,
                            profile=profile,
                        )
                    )
            emp_text = text[start:end].strip()
            if emp_text:
                actions.append(
                    SpeechAction(
                        action_type="speak",
                        text=emp_text,
                        rate=max(120, base_rate - 25),
                        volume=min(1.0, volume * 1.1),
                        style=style_name,
                        profile=profile,
                        emphasis=True,
                    )
                )
            last_idx = end
        if last_idx < len(text):
            trail_text = text[last_idx:].strip()
            if trail_text:
                actions.append(
                    SpeechAction(
                        action_type="speak",
                        text=trail_text,
                        rate=base_rate,
                        volume=volume,
                        style=style_name,
                        profile=profile,
                    )
                )

    # ------------------------------------------------------------------
    # Internal queue / worker
    # ------------------------------------------------------------------

    def _submit_request(self, req: SpeechRequest) -> None:
        """Submit a request to the queue, pre-empting previous ones if cancel_previous is set."""
        # Module 5: deduplication — drop if identical text just enqueued within DEDUP_WINDOW
        now = time.perf_counter()
        if (
            req.static_text
            and req.static_text == self._last_queued_text
            and (now - self._last_queued_time) < DEDUP_WINDOW
        ):
            logger.info(
                "[SPEECH DEDUP] Ignoring duplicate request for text='%s...'",
                (req.static_text or "")[:40],
            )
            req.status = SpeechStatus.CANCELLED
            req.completed_event.set()
            return

        if req.cancel_previous:
            self.cancel()

        if req.static_text:
            self._last_queued_text = req.static_text
            self._last_queued_time = now

        priority = 10 if req.profile in ("Warnings", "Error Messages") else 5
        self.queue.put((priority, req.submit_time, req))

    def _worker_loop(self) -> None:
        """Background thread executing speech requests."""
        try:
            import pythoncom  # type: ignore
            pythoncom.CoInitialize()
        except Exception:
            pass

        from voice.voice_engine import VoiceEngineV2

        self.voice_engine = VoiceEngineV2(use_pyttsx3=self.use_pyttsx3)
        self.engine = self.voice_engine.engine
        self.voices = self.voice_engine.voices

        while True:
            try:
                priority, submit_time, req = self.queue.get(block=True)

                if self.stop_event.is_set():
                    self.stop_event.clear()

                self.current_request = req
                self.is_playing = True
                req.queue_time = time.perf_counter() - req.submit_time
                req.status = SpeechStatus.STARTED

                # Issue 7: Voice latency metric — explicit queue_delay measurement
                queue_delay_ms = req.queue_time * 1000.0
                if queue_delay_ms > 250.0:
                    logger.warning(
                        "[VOICE LATENCY] Queue delay %.0fms exceeded 250ms target for id=%s",
                        queue_delay_ms,
                        req.request_id,
                    )
                else:
                    logger.info(
                        "[VOICE LATENCY] queue_delay=%.0fms id=%s",
                        queue_delay_ms,
                        req.request_id,
                    )

                logger.info("[SPEECH STARTED] id=%s", req.request_id)
                try:
                    from brain.event_bus import event_bus
                    event_bus.publish("SPEECH_STARTED", {"request_id": req.request_id, "text": req.static_text})
                except Exception:
                    pass

                if self.is_paused:
                    self.pause_event.clear()

                try:
                    if req.static_text:
                        self._play_text(req.static_text, req)
                    elif req.chunks_generator:
                        self._play_stream(req.chunks_generator, req)

                    # Mark success only if not already interrupted/cancelled
                    if req.status == SpeechStatus.STARTED:
                        req.status = SpeechStatus.SUCCESS
                except Exception as exc:
                    logger.error("[SPEECH FAILED] id=%s error=%s", req.request_id, exc)
                    req.status = SpeechStatus.FAILED

                try:
                    from brain.event_bus import event_bus
                    event_bus.publish("SPEECH_COMPLETED", {"request_id": req.request_id, "status": req.status.value})
                except Exception:
                    pass

                req.end_time = time.perf_counter()
                req.total_response_latency = req.end_time - req.submit_time

                # Module 8: record health stats
                self.health.record(req.status, req.total_response_latency)

                generation_time = getattr(req, "generation_time", 0.0)
                playback_latency = getattr(req, "playback_latency", 0.0)

                self.performance_logs.append(
                    {
                        "request_id": req.request_id,
                        "profile": req.profile,
                        "style": req.style,
                        "queue_time": req.queue_time,
                        "speech_latency": req.speech_latency,
                        "generation_time": generation_time,
                        "playback_latency": playback_latency,
                        "total_response_latency": req.total_response_latency,
                        "status": req.status.value,
                    }
                )

                logger.info(
                    "[SPEECH COMPLETED] id=%s status=%s latency=%.3fs (speech_latency=%.3fs, queue_time=%.3fs)",
                    req.request_id,
                    req.status.value,
                    req.total_response_latency,
                    req.speech_latency,
                    req.queue_time,
                )

                # Module 8: log health every 10 requests
                if self.health.total_requests % 10 == 0:
                    logger.info(self.health.get_report())

                self.is_playing = False
                self.current_request = None
                req.completed_event.set()
                self.queue.task_done()

            except Exception as e:
                logger.error("Error in SpeakingEngine worker loop: %s", e)
                time.sleep(0.1)

    def _play_text(self, text: str, req: SpeechRequest) -> None:
        """Analyze, parse, and speak a block of text."""
        profile = req.profile or self.detect_profile(text)
        req.profile = profile
        actions = self.parse_actions(text, profile, req.style)

        for action in actions:
            if self.stop_event.is_set():
                req.status = SpeechStatus.INTERRUPTED
                break
            self.pause_event.wait()

            if req.start_time is None:
                req.start_time = time.perf_counter()
                req.speech_latency = req.start_time - req.submit_time

            self._execute_action(action, req)

    def _play_stream(self, generator: Generator[str, None, None], req: SpeechRequest) -> None:
        """Play stream chunks as they arrive."""
        buffer = ""
        profile = req.profile or "General Chat"
        req.profile = profile

        try:
            for chunk in generator:
                if self.stop_event.is_set():
                    req.status = SpeechStatus.INTERRUPTED
                    break
                self.pause_event.wait()
                buffer += chunk
                if any(p in chunk for p in [".", "!", "?", "\n"]):
                    self._play_text(buffer, req)
                    buffer = ""
            if buffer.strip() and not self.stop_event.is_set():
                self._play_text(buffer, req)
        except Exception as e:
            logger.error("Error streaming speech chunks: %s", e)

    def _execute_action(self, action: SpeechAction, req: Optional[SpeechRequest] = None) -> None:
        """Run single speech action with retry logic (Module 2) and watchdog (Module 3)."""
        self.spoken_actions_log.append(action)

        if action.action_type == "pause":
            time.sleep(action.duration * self.sleep_multiplier)
        elif action.action_type == "speak":
            logger.info(
                "Speaking (%s/rate=%d/vol=%.1f/profile=%s): %s",
                action.style, action.rate, action.volume, action.profile, action.text,
            )
            print(f"Speaking: {action.text}")

            # Module 2: retry loop with exponential backoff
            last_exc: Optional[Exception] = None
            for attempt in range(1, MAX_RETRIES + 1):
                if self.stop_event.is_set():
                    break
                try:
                    metrics = self._speak_action_with_watchdog(action)
                    # Propagate metrics to current request
                    if req is not None and self.current_request is not None:
                        if not hasattr(self.current_request, "generation_time"):
                            self.current_request.generation_time = 0.0
                        if not hasattr(self.current_request, "playback_latency"):
                            self.current_request.playback_latency = 0.0
                        self.current_request.generation_time += metrics["generation_time"]
                        if self.current_request.playback_latency == 0.0:
                            self.current_request.playback_latency = metrics["playback_latency"]
                    return  # success — no retry needed
                except Exception as exc:
                    last_exc = exc
                    self.health.record_retry()
                    if attempt < MAX_RETRIES:
                        delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                        logger.info(
                            "[RETRY] attempt=%d/%d id=%s delay=%.2fs reason=%s",
                            attempt, MAX_RETRIES,
                            req.request_id if req else "?",
                            delay,
                            exc,
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            "[SPEECH FAILED] id=%s all %d retries exhausted: %s",
                            req.request_id if req else "?",
                            MAX_RETRIES,
                            exc,
                        )

            # Module 7: all retries failed — activate fallback TTS
            if last_exc is not None and not self.stop_event.is_set():
                self._speak_via_fallback(action.text)

    def _speak_action_with_watchdog(self, action: SpeechAction) -> Dict[str, Any]:
        """
        Module 3: Run voice_engine.speak_action() on the worker thread (which has COM initialized),
        and spawn a watchdog timer to call engine.stop() if it hangs.
        """
        timeout_occurred = False
        timer = None

        def _on_timeout() -> None:
            nonlocal timeout_occurred
            timeout_occurred = True
            logger.error(
                "[SPEECH TIMEOUT] Utterance exceeded %.1fs: '%s'",
                SPEECH_TIMEOUT,
                action.text[:60],
            )
            # Call stop() on the voice engine to break the runAndWait() loop
            if self.voice_engine and self.voice_engine.engine:
                try:
                    self.voice_engine.engine.stop()
                except Exception as exc:
                    logger.error("Error stopping engine on timeout: %s", exc)
            self.stop_event.set()
            if self.current_request:
                self.current_request.status = SpeechStatus.TIMEOUT
            self.health.timeout_count += 1

        # Start watchdog timer
        timer = threading.Timer(SPEECH_TIMEOUT, _on_timeout)
        timer.start()

        try:
            result = self.voice_engine.speak_action(
                text=action.text,
                rate=action.rate,
                volume=action.volume,
                profile=action.profile,
                style=action.style,
                sleep_multiplier=self.sleep_multiplier,
                stop_check_func=self.stop_event.is_set,
            )
            if timeout_occurred:
                raise TimeoutError(f"Speech timed out after {SPEECH_TIMEOUT}s")
            return result
        finally:
            if timer is not None:
                timer.cancel()

    def _speak_via_fallback(self, text: str) -> None:
        """Module 7: Activate fallback TTS when primary engine has exhausted retries."""
        logger.info("[FALLBACK ACTIVATED] Primary TTS failed — switching to SAPI.SpVoice for: '%s...'", text[:60])
        try:
            from voice.fallback_tts import get_fallback_tts
            fb = get_fallback_tts()
            if fb.available:
                ok = fb.speak(text)
                if ok:
                    logger.info("[FALLBACK TTS] Successfully spoke via SAPI fallback.")
                else:
                    logger.error("[FALLBACK TTS] Fallback also failed — response lost: '%s...'", text[:60])
            else:
                logger.error("[FALLBACK TTS] Not available — response lost: '%s...'", text[:60])
        except Exception as exc:
            logger.error("[FALLBACK TTS] Exception during fallback: %s", exc)
