from __future__ import annotations

import json
import logging
import time
import os
import threading
from typing import Any, Optional

import requests

from config.llm import HOST, MODEL, TIMEOUT
from providers.provider_base import ProviderBase
from voice.speaker import speak

logger = logging.getLogger(__name__)


class OllamaProvider(ProviderBase):
    """Generate text using a local Ollama HTTP server with high-performance streaming."""

    def __init__(
        self,
        *,
        host: str = HOST,
        model: str = MODEL,
        timeout: int = TIMEOUT,
    ) -> None:
        self.host = host
        self.model = model
        self.timeout = timeout
        
        # Task 3: Persistent HTTP Session
        self.session = requests.Session()
        
        # Task 9: Concurrency Control
        self.lock = threading.Lock()
        
        # Task 6: Caching
        self._cache: dict[str, str] = {}
        
        # Task 8: Hardware Optimization
        self.num_thread = max(1, (os.cpu_count() or 4) - 1)

    def generate(self, text: str, *, context: Optional[dict[str, Any]] = None) -> str:
        prompt = text
        url = f"{self.host}/api/generate"

        start = time.perf_counter()
        
        try:
            logger.info("Ollama prompt: %s", prompt)
            logger.info("Ollama model: %s", self.model)

            lowered = (text or "").lower()
            wants_detail = any(
                kw in lowered
                for kw in ["explain", "detailed", "in depth", "teach me"]
            )
            
            # Keep responses short by default.
            num_predict = 180 if wants_detail else 80
            temperature = 0.5
            
            # Task 4: Prompt Optimization
            # Reduced the system prompt slightly to reduce token count
            system_prompt = "You are Khushi AI. Answer in 2-4 concise sentences.\n"

            if context and context.get("emotional_state") is not None:
                state = context["emotional_state"]
                if hasattr(state, "primary_emotion"):
                    system_prompt += "Never claim emotions (no 'I feel', 'I am sad'). Tone: "
                    if state.primary_emotion == "sadness":
                        system_prompt += "Supportive, calm.\n"
                    elif state.primary_emotion == "stress":
                        system_prompt += "Calm, structured.\n"
                    elif state.primary_emotion == "frustration":
                        system_prompt += "Objective, patient.\n"
                    elif state.primary_emotion == "burnout":
                        system_prompt += "Supportive, encouraging of rest.\n"
                    elif state.primary_emotion == "celebration":
                        system_prompt += "Supportive, reinforcing.\n"
                    else:
                        system_prompt += "Professional, calm.\n"

            prompt_with_instructions = f"{system_prompt}\nUser: {text}\nAssistant:"
            
            # Task 6: Check Cache
            if prompt_with_instructions in self._cache:
                logger.info("Ollama CACHE HIT for prompt.")
                cached_resp = self._cache[prompt_with_instructions]
                # To maintain identical behavior, we can speak it
                import voice.speaker as speaker_module
                speaker_module._has_spoken_in_turn = True
                speak(cached_resp, cancel_previous=True, block=False)
                return cached_resp

            # Task 9: Enforce Single Concurrency Queue
            with self.lock:
                # Task 7 & 8: Optimized generation parameters including keep_alive
                payload = {
                    "model": self.model,
                    "prompt": prompt_with_instructions,
                    "stream": True,  # Task 5: Streaming API
                    "keep_alive": -1,  # Task 2: Keep model loaded
                    "options": {
                        "num_predict": num_predict,
                        "temperature": temperature,
                        "num_thread": self.num_thread
                    }
                }

                resp = self.session.post(
                    url,
                    json=payload,
                    timeout=self.timeout,
                    stream=True
                )
                
                resp.raise_for_status()

                # Task 10: Metrics tracking
                first_token_time = None
                total_tokens = 0
                
                full_text = ""
                sentence_buffer = ""
                
                import voice.speaker as speaker_module
                
                # Task 5: Begin speaking while tokens arrive
                for line in resp.iter_lines():
                    if line:
                        if first_token_time is None:
                            first_token_time = time.perf_counter()
                            ttft = first_token_time - start
                            logger.info("Ollama TTFT (Time to First Token): %.3fs", ttft)
                            
                        chunk_data = json.loads(line)
                        chunk = chunk_data.get("response", "")
                        
                        if chunk:
                            full_text += chunk
                            sentence_buffer += chunk
                            total_tokens += 1
                            
                            # Publish stream token for GUI display
                            try:
                                from brain.event_bus import event_bus
                                event_bus.publish("STREAM_TOKEN", {"token": chunk, "full_text": full_text})
                            except Exception:
                                pass
                            
                            # Speak on punctuation
                            if any(p in chunk for p in [".", "!", "?", "\n"]):
                                if sentence_buffer.strip():
                                    speaker_module._has_spoken_in_turn = True
                                    speak(sentence_buffer.strip(), cancel_previous=False, block=False)
                                sentence_buffer = ""
                        
                        if chunk_data.get("done"):
                            break
                            
                # Speak any remaining buffer
                if sentence_buffer.strip():
                    speaker_module._has_spoken_in_turn = True
                    speak(sentence_buffer.strip(), cancel_previous=False, block=False)
                    
                elapsed = time.perf_counter() - start
                logger.info("Ollama response time: %.3fs", elapsed)
                if first_token_time and elapsed > (first_token_time - start):
                    tokens_per_sec = total_tokens / (elapsed - (first_token_time - start))
                    logger.info("Ollama Tokens/sec: %.2f", tokens_per_sec)
                
                logger.info("Ollama total latency: %.3fs", elapsed)
                
                # Update Cache
                if full_text:
                    self._cache[prompt_with_instructions] = full_text
                    
                return full_text

        except requests.exceptions.ConnectTimeout:
            logger.exception("Ollama connection timeout")
            return "Ollama connection timed out."
        except requests.exceptions.ConnectionError:
            logger.exception("Ollama connection refused/unreachable")
            return "Ollama is not running or connection was refused."
        except requests.exceptions.Timeout:
            logger.exception("Ollama request timed out")
            return "Ollama request timed out."
        except Exception as exc:
            logger.exception("Ollama provider failed: %s", exc)
            return "Ollama failed to generate a response."

