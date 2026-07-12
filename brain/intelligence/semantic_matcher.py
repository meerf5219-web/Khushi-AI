from __future__ import annotations

"""
Module 4: Semantic Intent Matcher
===================================
Uses sentence embeddings (sentence-transformers) to match user queries to intents
by semantic similarity rather than exact phrase matching.

Graceful fallback:
- If sentence-transformers is not installed, falls back to keyword TF-IDF scoring.
- The fallback is robust enough to handle most queries correctly.

Caching:
- Intent vectors are computed ONCE at startup and cached in memory.
- User query vectors are NOT cached (each query is unique).

Model: sentence-transformers/all-MiniLM-L6-v2 (22MB, fast, offline after first download)
"""

import hashlib
import logging
import math
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Intent canonical phrases (used for embedding comparison)
# Maps intent_name → list of representative phrases
# ---------------------------------------------------------------------------
_INTENT_PHRASES: Dict[str, List[str]] = {
    "COMPANION_REFLECT": [
        "how am i doing", "review my progress", "give me a reflection",
        "what did i do this week", "daily reflection", "weekly reflection",
        "how have i been doing", "summarize my progress",
    ],
    "COMPANION_RECOMMEND": [
        "what should i focus on today", "what should i study",
        "give me a recommendation", "what do you recommend",
        "what is my next step", "help me prioritize", "suggest something",
        "what should i work on",
    ],
    "COMPANION_PROFILE": [
        "show my profile", "who am i", "tell me about myself",
        "what is my profile", "show my full profile",
    ],
    "COMPANION_TIMELINE": [
        "show my timeline", "show my history", "my life timeline",
        "what events do i have", "show timeline",
    ],
    "LIFE_MEMORY_GOALS": [
        "show my goals", "what are my goals", "my objectives",
        "what goals do i have", "list my goals",
    ],
    "LIFE_MEMORY_PROJECTS": [
        "show my projects", "what projects am i working on",
        "list my projects", "what am i building",
    ],
    "LIFE_MEMORY_HABITS": [
        "show my habits", "what are my habits", "list my habits",
    ],
    "LIFE_MEMORY_PREFERENCES": [
        "show my preferences", "what are my preferences", "my likes",
    ],
    "RECALL_NAME": [
        "what is my name", "tell me my name", "who am i", "do you know my name",
        "what did i tell you my name was",
    ],
    "OPEN_APP": [
        "open chrome", "launch notepad", "start calculator",
        "open an application", "launch the app",
    ],
    "SEARCH": [
        "search for python", "google something", "look up information",
        "search the internet",
    ],
    "WEB_SEARCH": [
        "what is the latest news", "current weather", "what happened today",
        "search online for", "find on the web",
    ],
    "KNOWLEDGE_QUERY": [
        "what does my document say", "search my notes", "find in my files",
        "what is written in my notebook",
    ],
    "CALCULATE": [
        "calculate two plus two", "what is five times eight",
        "compute the result", "math calculation",
    ],
    "TIME": [
        "what time is it", "current time", "tell me the time",
    ],
    "DATE": [
        "what is today's date", "what day is it", "current date",
    ],
    "GREETING": [
        "hello", "hi there", "good morning", "hey khushi",
    ],
    "GOODBYE": [
        "goodbye", "bye", "see you later", "farewell",
    ],
    "REMEMBER": [
        "remember my name is faisal", "remember that i like python",
        "remember my goal is upsc", "save this information",
    ],
    "SCREENSHOT": [
        "take a screenshot", "capture the screen", "screenshot please",
    ],
    "SYSTEM": [
        "check battery", "how much ram is used", "cpu usage",
        "system information", "disk space",
    ],
    "NOTE_CREATE": [
        "take a note", "remember this note", "create a note",
    ],
    "NOTE_SHOW": [
        "show my notes", "list notes", "what notes do i have",
    ],
    "WEATHER": [
        "check the weather", "what is the weather", "weather today",
        "weather in delhi", "what is the temperature", "is it going to rain",
        "weather forecast", "tell me the weather", "how is the weather",
        "weather outside", "current temperature", "will it rain today",
        "what is the weather like", "weather report", "should i carry an umbrella",
        "what's the weather", "today's weather",
    ],
    "GENERAL_QUERY": [
        "who is einstein", "what is machine learning", "explain quantum physics",
        "tell me about history", "how does python work",
    ],
}

# Map semantic intent names to actual routing intents
_SEMANTIC_TO_ROUTING: Dict[str, str] = {
    "COMPANION_REFLECT": "COMPANION_REFLECT",
    "COMPANION_RECOMMEND": "COMPANION_RECOMMEND",
    "COMPANION_PROFILE": "COMPANION_PROFILE",
    "COMPANION_TIMELINE": "COMPANION_TIMELINE",
    "LIFE_MEMORY_GOALS": "LIFE_MEMORY",
    "LIFE_MEMORY_PROJECTS": "LIFE_MEMORY",
    "LIFE_MEMORY_HABITS": "LIFE_MEMORY",
    "LIFE_MEMORY_PREFERENCES": "LIFE_MEMORY",
    "RECALL_NAME": "RECALL_MEMORY",
    "OPEN_APP": "OPEN_APP",
    "SEARCH": "SEARCH",
    "WEB_SEARCH": "WEB_SEARCH",
    "KNOWLEDGE_QUERY": "KNOWLEDGE_QUERY",
    "CALCULATE": "CALCULATE",
    "TIME": "TIME",
    "DATE": "DATE",
    "GREETING": "GREETING",
    "GOODBYE": "GOODBYE",
    "REMEMBER": "LIFE_MEMORY",
    "SCREENSHOT": "SYSTEM",
    "SYSTEM": "SYSTEM",
    "NOTE_CREATE": "NOTE_CREATE",
    "NOTE_SHOW": "NOTE_SHOW",
    "WEATHER": "WEATHER",
    "GENERAL_QUERY": "GENERAL_QUERY",
}


@dataclass
class SemanticMatch:
    intent: str
    routing_intent: str
    score: float
    matched_phrase: str
    engine: str  # "transformer" or "keyword"


# ---------------------------------------------------------------------------
# Keyword-based fallback scorer (no external deps)
# ---------------------------------------------------------------------------

def _keyword_score(query: str, phrases: List[str]) -> float:
    """TF-IDF-inspired keyword overlap score between query and candidate phrases."""
    query_words = set(query.lower().split())
    if not query_words:
        return 0.0

    best = 0.0
    for phrase in phrases:
        phrase_words = set(phrase.lower().split())
        if not phrase_words:
            continue
        # Jaccard similarity
        intersection = len(query_words & phrase_words)
        union = len(query_words | phrase_words)
        score = intersection / union if union > 0 else 0.0
        # Boost if query is a substring of phrase or vice versa
        if query.lower() in phrase.lower() or phrase.lower() in query.lower():
            score = max(score, 0.8)
        best = max(best, score)
    return best


# Global SentenceTransformer model cache to prevent expensive reloads across tests/instances
_SHARED_MODEL: Optional[Any] = None
_MODEL_LOCK = threading.Lock()


class SemanticIntentMatcher:
    """
    Semantic intent matcher with transformer + keyword fallback.

    On first instantiation, loads the sentence-transformer model (if available).
    Intent phrase embeddings are cached after first computation.
    """

    def __init__(self) -> None:
        self._model: Optional[Any] = None
        self._use_transformers = False
        self._intent_embeddings: Optional[Dict[str, Any]] = None
        self._intent_phrases: Dict[str, List[str]] = _INTENT_PHRASES
        self._model_loaded = False

    def _try_load_model(self) -> None:
        """Attempt to load sentence-transformers model. Gracefully fails."""
        import os
        if os.environ.get("DISABLE_TRANSFORMERS") == "1":
            logger.info("SemanticMatcher: sentence-transformers disabled via environment variable; using keyword fallback.")
            return

        global _SHARED_MODEL
        if _SHARED_MODEL is not None:
            self._model = _SHARED_MODEL
            self._use_transformers = True
            self._precompute_intent_embeddings()
            return

        with _MODEL_LOCK:
            if _SHARED_MODEL is not None:  # double-checked locking
                self._model = _SHARED_MODEL
                self._use_transformers = True
                self._precompute_intent_embeddings()
                return

            try:
                from sentence_transformers import SentenceTransformer  # type: ignore
                logger.info("SemanticMatcher: loading sentence-transformer model (offline-first)...")
                t0 = time.perf_counter()
                try:
                    # Issue 5: load from local cache without any network HEAD request
                    model = SentenceTransformer(
                        "sentence-transformers/all-MiniLM-L6-v2",
                        local_files_only=True,
                    )
                    logger.info("SemanticMatcher: model loaded from local cache (no network).")
                except Exception:
                    # Model not cached yet — do a one-time network download
                    logger.info("SemanticMatcher: local cache miss — downloading model once.")
                    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
                
                _SHARED_MODEL = model
                self._model = model
                self._use_transformers = True
                elapsed = time.perf_counter() - t0
                logger.info("SemanticMatcher: model loaded in %.2fs", elapsed)
                self._precompute_intent_embeddings()
            except ImportError:
                logger.warning("SemanticMatcher: sentence-transformers not available; using keyword fallback.")
            except Exception as exc:
                logger.warning("SemanticMatcher: model load failed (%s); using keyword fallback.", exc)


    def _precompute_intent_embeddings(self) -> None:
        """Pre-compute and cache embeddings for all intent phrases."""
        if not self._use_transformers or self._model is None:
            return
        try:
            import numpy as np  # type: ignore
            t0 = time.perf_counter()
            embeddings: Dict[str, Any] = {}
            for intent, phrases in self._intent_phrases.items():
                vecs = self._model.encode(phrases, convert_to_numpy=True, show_progress_bar=False)
                # Store mean embedding as the canonical intent vector
                embeddings[intent] = np.mean(vecs, axis=0)
            self._intent_embeddings = embeddings
            elapsed = time.perf_counter() - t0
            logger.info("SemanticMatcher: intent embeddings precomputed in %.2fs", elapsed)
        except Exception as exc:
            logger.warning("SemanticMatcher: embedding precompute failed (%s); falling back.", exc)
            self._use_transformers = False
            self._intent_embeddings = None

    def _cosine_similarity(self, a: Any, b: Any) -> float:
        """Compute cosine similarity between two numpy arrays."""
        try:
            import numpy as np  # type: ignore
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return float(np.dot(a, b) / (norm_a * norm_b))
        except Exception:
            return 0.0

    def match(self, query: str, *, top_k: int = 3) -> List[SemanticMatch]:
        """
        Find the top-k best intent matches for a query.

        Returns list of SemanticMatch sorted by score descending.
        """
        if not query:
            return []
            
        if not self._model_loaded:
            self._try_load_model()
            self._model_loaded = True

        if self._use_transformers and self._model is not None and self._intent_embeddings:
            return self._match_transformer(query, top_k=top_k)
        else:
            return self._match_keyword(query, top_k=top_k)

    def _match_transformer(self, query: str, *, top_k: int) -> List[SemanticMatch]:
        """Transformer-based cosine similarity matching."""
        try:
            t0 = time.perf_counter()
            query_vec = self._model.encode([query], convert_to_numpy=True, show_progress_bar=False)[0]
            elapsed = time.perf_counter() - t0
            logger.debug("SemanticMatcher: query encoded in %.4fs", elapsed)

            scores: List[Tuple[str, float]] = []
            for intent, intent_vec in self._intent_embeddings.items():
                sim = self._cosine_similarity(query_vec, intent_vec)
                scores.append((intent, sim))

            scores.sort(key=lambda x: x[1], reverse=True)
            results = []
            for intent, score in scores[:top_k]:
                results.append(SemanticMatch(
                    intent=intent,
                    routing_intent=_SEMANTIC_TO_ROUTING.get(intent, intent),
                    score=score,
                    matched_phrase=self._intent_phrases[intent][0],
                    engine="transformer",
                ))
            logger.info(
                "SemanticMatcher[transformer]: query='%s' top_match=%s score=%.3f",
                query, results[0].intent if results else "none", results[0].score if results else 0.0,
            )
            return results
        except Exception as exc:
            logger.warning("SemanticMatcher: transformer match failed (%s); falling back.", exc)
            return self._match_keyword(query, top_k=top_k)

    def _match_keyword(self, query: str, *, top_k: int) -> List[SemanticMatch]:
        """Keyword-based fallback matching."""
        scores: List[Tuple[str, float, str]] = []
        for intent, phrases in self._intent_phrases.items():
            score = _keyword_score(query, phrases)
            # Find which phrase matched best
            best_phrase = max(phrases, key=lambda p: _keyword_score(query, [p]))
            scores.append((intent, score, best_phrase))

        scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for intent, score, phrase in scores[:top_k]:
            results.append(SemanticMatch(
                intent=intent,
                routing_intent=_SEMANTIC_TO_ROUTING.get(intent, intent),
                score=score,
                matched_phrase=phrase,
                engine="keyword",
            ))

        if results:
            logger.info(
                "SemanticMatcher[keyword]: query='%s' top_match=%s score=%.3f",
                query, results[0].intent, results[0].score,
            )
        return results

    def best_match(self, query: str) -> Optional[SemanticMatch]:
        """Return the single best match, or None if score is too low."""
        matches = self.match(query, top_k=1)
        if matches and matches[0].score > 0.1:
            return matches[0]
        return None
