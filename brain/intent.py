from __future__ import annotations

from typing import Any, Dict, Optional


class IntentEngine:
    """Classify user input into an intent object with optional entity data."""

    def detect(self, text: str) -> Dict[str, Any]:
        """Return a structured intent payload for the provided text."""
        normalized_text = text.lower().strip()

        # =========================
        # Companion Memory (LIFE_MEMORY) - classification only (Milestone 1)
        # =========================
        # Explicit STORE/UPDATE/DELETE commands
        explicit_prefixes = [
            "remember that ",
            "remember my ",
            "forget that ",
            "forget ",
            "update ",
            "change ",
            "remove ",
            "delete memory",
            "delete that ",
            "save this ",
            "store this ",
        ]
        if any(normalized_text.startswith(p) for p in explicit_prefixes):
            action = "STORE"
            if normalized_text.startswith("forget") or normalized_text.startswith("remove") or normalized_text.startswith("delete"):
                action = "DELETE"

            # Category hint (foundation rules; no storage yet)
            category = "identity"
            if any(k in normalized_text for k in ["goal", "goals"]):
                category = "GOALS"
            elif any(k in normalized_text for k in ["habit", "habits"]):
                category = "HABITS"
            elif any(k in normalized_text for k in ["project", "projects"]):
                category = "PROJECTS"
            elif any(k in normalized_text for k in ["preference", "preferences", "favourite", "favorite"]):
                category = "PREFERENCES"
            elif any(k in normalized_text for k in ["vehicle", "car", "bike", "vehicle(s)"]):
                category = "VEHICLES"
            elif any(k in normalized_text for k in ["device", "devices"]):
                category = "DEVICES"
            elif any(k in normalized_text for k in ["education", "graduated", "b.pharmacy", "b pharmacy", "school", "college"]):
                category = "EDUCATION"
            elif any(k in normalized_text for k in ["career", "selected", "inspector", "job", "role"]):
                category = "CAREER"
            elif any(k in normalized_text for k in ["timeline", "life event", "event"]):
                category = "LIFE_EVENTS"

            # Extract entity as remaining text (target/content)
            target = normalized_text

            payload = {
                "action": action,
                "category": category,
                "target": target,
                "confidence": 0.98,
                "raw_text": text,
                "metadata": {},
            }
            return {
                "intent": "LIFE_MEMORY",
                "entity": payload,
            }

        # =========================
        # Companion Intelligence queries (must come before LIFE_MEMORY read_queries)
        # =========================
        _reflect_phrases = [
            "how am i doing",
            "how have i been doing",
            "give me a reflection",
            "daily reflection",
            "weekly reflection",
            "monthly reflection",
            "show my reflection",
            "what did i do this week",
            "what did i do today",
            "what have i done",
            "review my progress",
        ]
        if any(q in normalized_text for q in _reflect_phrases):
            return {"intent": "COMPANION_REFLECT", "entity": {"query": normalized_text}}

        _recommend_phrases = [
            "what should i focus on",
            "what should i do today",
            "what should i study",
            "give me a recommendation",
            "what do you recommend",
            "recommend something",
            "what are my recommendations",
            "suggest something",
            "what's my next step",
            "what is my next step",
            "help me prioritize",
            "what should i work on",
        ]
        if any(q in normalized_text for q in _recommend_phrases):
            return {"intent": "COMPANION_RECOMMEND", "entity": {"query": normalized_text}}

        _profile_phrases = [
            "show my profile",
            "show my full profile",
            "what is my profile",
            "who am i",
        ]
        if any(q in normalized_text for q in _profile_phrases):
            return {"intent": "COMPANION_PROFILE", "entity": {"query": normalized_text}}

        _timeline_phrases = [
            "show my timeline",
            "show timeline",
            "show my history",
            "my life timeline",
        ]
        if any(q in normalized_text for q in _timeline_phrases):
            return {"intent": "COMPANION_TIMELINE", "entity": {"query": normalized_text}}

        _status_phrases = [
            "companion status",
            "intelligence status",
            "companion summary",
            "session summary",
        ]
        if any(q in normalized_text for q in _status_phrases):
            return {"intent": "COMPANION_STATUS", "entity": {"query": normalized_text}}

        # Read-only queries for LIFE_MEMORY buckets
        read_queries = [
            "what are my goals",
            "show my goals",
            "show my projects",
            "what projects am i working on",
            "show my habits",
            "show my preferences",
            "show my preference",
        ]
        if any(q in normalized_text for q in read_queries):
            # Determine category
            category = "IDENTITY"
            if "goals" in normalized_text:
                category = "GOALS"
            elif "projects" in normalized_text:
                category = "PROJECTS"
            elif "habits" in normalized_text:
                category = "HABITS"
            elif "preferences" in normalized_text or "preference" in normalized_text:
                category = "PREFERENCES"

            payload = {
                "action": "READ",
                "category": category,
                "target": normalized_text,
                "confidence": 0.92,
                "raw_text": text,
                "metadata": {},
            }
            return {
                "intent": "LIFE_MEMORY",
                "entity": payload,
            }

        if normalized_text.startswith("remember"):
            content = normalized_text.replace("remember", "", 1).strip()
            if " is " in content:
                key, value = content.split(" is ", 1)
                return {
                    "intent": "REMEMBER",
                    "entity": {"key": key.strip(), "value": value.strip()},
                }

        if normalized_text.startswith("my favourite") or normalized_text.startswith("i live in") or normalized_text.startswith("i study") or (
            normalized_text.startswith("i am") and "years old" in normalized_text
        ):
            return {"intent": "SAVE_MEMORY", "entity": text}

        if "what is my favourite" in normalized_text or "what is my favorite" in normalized_text or "where do i live" in normalized_text or "what do i study" in normalized_text or "how old am i" in normalized_text or "what is my age" in normalized_text:
            return {"intent": "RECALL_MEMORY", "entity": text}

        if normalized_text.startswith("my name is"):
            name = normalized_text.replace("my name is", "", 1).strip().title()
            return {"intent": "NAME", "entity": name}

        # General knowledge queries (should not be classified as GREETING).
        general_query_prefixes = (
            "who is ",
            "who was ",
            "what is ",
            "what was ",
            "where is ",
            "where was ",
            "when ",
            "why ",
            "how ",
            "explain ",
            "tell me about ",
        )
        if any(normalized_text.startswith(p) for p in general_query_prefixes):
            return {"intent": "GENERAL_QUERY", "entity": None}

        # Web search intents (internet answers/news/weather/etc.).
        # NOTE: Do NOT include "search" / "find" here because those are handled by
        # explicit SEARCH / FILE_SEARCH intents below (unit-test expectations).
        if any(
            word in normalized_text
            for word in [
                "latest",
                "today",
                "current",
                "news",
                "who won",
                "weather",
                "temperature",
                "forecast",
            ]
        ):
            return {"intent": "WEB_SEARCH", "entity": None}

        # Knowledge Base (RAG): broad document-query detection (Option B).
        # Insert before SEARCH/FILE_SEARCH so "search my notes / find in my documents"
        # becomes KNOWLEDGE_QUERY.
        if self._is_knowledge_query(normalized_text):
            knowledge_entity = self._classify_knowledge_intent(normalized_text)
            if knowledge_entity is not None:
                return {"intent": "KNOWLEDGE_QUERY", "entity": knowledge_entity}

        if any(word in normalized_text for word in ["open", "launch", "start"]):
            entity = self._extract_app_name(normalized_text)
            return {"intent": "OPEN_APP", "entity": entity}

        if any(word in normalized_text for word in ["time", "clock"]):
            return {"intent": "TIME"}

        if "date" in normalized_text:
            return {"intent": "DATE"}

        if any(word in normalized_text for word in ["search", "google"]):
            entity = self._extract_search_query(normalized_text)
            return {"intent": "SEARCH", "entity": entity}

        if any(word in normalized_text for word in ["find", "locate"]):
            return {"intent": "FILE_SEARCH", "entity": self._extract_file_query(normalized_text)}

        if "create folder" in normalized_text:
            return {"intent": "FILE", "entity": self._extract_file_action(normalized_text, "create_folder")}

        if "create file" in normalized_text:
            return {"intent": "FILE", "entity": self._extract_file_action(normalized_text, "create_file")}

        if "open folder" in normalized_text:
            return {"intent": "FILE", "entity": self._extract_file_action(normalized_text, "open_folder")}

        if "delete file" in normalized_text:
            return {"intent": "FILE", "entity": self._extract_file_action(normalized_text, "delete_file")}

        if "list files" in normalized_text:
            return {"intent": "FILE", "entity": self._extract_file_action(normalized_text, "list_files")}

        if any(phrase in normalized_text for phrase in ["take screenshot", "screenshot", "capture screen", "capture"]):
            return {"intent": "SYSTEM", "entity": "take_screenshot"}

        if any(word in normalized_text for word in ["battery", "cpu", "ram", "disk", "uptime"]):
            return {"intent": "SYSTEM", "entity": self._extract_system_query(normalized_text)}

        if any(word in normalized_text for word in ["copy", "paste", "clipboard"]):
            return {"intent": "CLIPBOARD", "entity": self._extract_clipboard_action(normalized_text)}

        if "volume up" in normalized_text or "increase volume" in normalized_text:
            return {"intent": "SYSTEM", "entity": "volume_up"}

        if "volume down" in normalized_text or "decrease volume" in normalized_text:
            return {"intent": "SYSTEM", "entity": "volume_down"}

        if "mute" in normalized_text:
            return {"intent": "SYSTEM", "entity": "mute"}

        if "lock computer" in normalized_text or "lock pc" in normalized_text:
            return {"intent": "SYSTEM", "entity": "lock_pc"}

        if "show desktop" in normalized_text:
            return {"intent": "SYSTEM", "entity": "show_desktop"}

        if any(word in normalized_text for word in ["brightness", "bright"]):
            return {"intent": "BRIGHTNESS", "entity": self._extract_brightness_action(normalized_text)}

        if any(word in normalized_text for word in ["weather", "temperature", "forecast"]):
            return {"intent": "WEATHER"}

        if any(word in normalized_text for word in ["calculate", "calculator", "+", "-", "*", "/", "%", "(", ")"]):
            return {"intent": "CALCULATE", "entity": self._extract_expression(normalized_text)}

        if any(word in normalized_text for word in ["take note", "remember this note", "remember note"]):
            return {"intent": "NOTE_CREATE"}

        if any(word in normalized_text for word in ["show notes", "show note", "list notes"]):
            return {"intent": "NOTE_SHOW"}

        if any(word in normalized_text for word in ["delete notes", "delete note", "clear notes"]):
            return {"intent": "NOTE_DELETE"}

        if any(word in normalized_text for word in ["hello", "hi"]):
            return {"intent": "GREETING"}

        if any(word in normalized_text for word in ["bye", "goodbye"]):
            return {"intent": "GOODBYE"}

        return {"intent": "CHAT"}

    def _extract_app_name(self, text: str) -> Optional[str]:
        """Extract an application name from the input text."""
        for app in ["chrome", "notepad", "calculator", "paint"]:
            if app in text:
                return app
        return None

    def _extract_search_query(self, text: str) -> Optional[str]:
        """Extract a search query from the input text."""
        for keyword in ["search", "google"]:
            if keyword in text:
                query = text.replace(keyword, "", 1).strip()
                return query or None
        return None

    def _extract_file_query(self, text: str) -> Optional[str]:
        """Extract a file name or pattern from the input text."""
        for keyword in ["find", "locate"]:
            if keyword in text:
                return text.replace(keyword, "", 1).strip() or None
        return None

    def _extract_system_query(self, text: str) -> Optional[str]:
        """Extract the requested system metric from the input text."""
        for metric in ["battery", "cpu", "ram", "disk", "uptime"]:
            if metric in text:
                return metric
        return None

    def _extract_file_action(self, text: str, action: str) -> Optional[str]:
        """Extract the target path or name for a file action."""
        for prefix in ["create folder", "create file", "open folder", "delete file", "list files"]:
            if prefix in text:
                return text.replace(prefix, "", 1).strip() or None
        return action if not text else None

    def _is_knowledge_query(self, normalized_text: str) -> bool:
        """Return True if the message likely refers to user documents/notes."""
        if not normalized_text:
            return False

        # Document/source signals (Option B).
        doc_signals = [
            "my notes",
            "my notebook",
            "my book",
            "my pdf",
            "my document",
            "my documents",
            "my files",
            "from my",
            "in my",
            "according to my",
            "search my",
            "find in my",
            "what does my",
            "summarize my",
            "compare from my",
            "my pharmacology",
            "my economics",
            "my upsc",
            "my federalism",
        ]

        # Query/action signals (phrases indicating retrieval/summarization).
        query_signals = [
            "what does",
            "what is written",
            "what does my",
            "explain",
            "summarize",
            "compare",
            "search",
            "find in",
            "according to",
            "in my",
            "from my",
            "what did i study",
            "what is written in my",
            "tell me",
        ]

        has_doc_signal = any(sig in normalized_text for sig in doc_signals)
        has_query_signal = any(sig in normalized_text for sig in query_signals)

        # If it explicitly includes doc signals + a question/action, it's knowledge.
        if has_doc_signal and has_query_signal:
            return True

        # Also allow "Article 32 in my documents" style.
        weak_doc_signals = ["my", "notebook", "pdf", "document", "documents", "notes", "book", "files"]
        has_any_doc_weak = any(sig in normalized_text for sig in weak_doc_signals)
        question_like = any(q in normalized_text for q in ["?", "summarize", "explain", "compare", "find", "search"])

        return bool(has_any_doc_weak and question_like)

    def _classify_knowledge_intent(self, normalized_text: str) -> Optional[Dict[str, str]]:
        """Return optional entity hint. If confidence is low, return None (so LLM can ask)."""
        # Low-confidence heuristic:
        # - require at least one strong document signal OR multiple weak doc signals
        # - require an explicit retrieval intent word.
        strong_signals = [
            "my notes",
            "my notebook",
            "my pdf",
            "my document",
            "my documents",
            "my files",
            "from my",
            "in my",
            "according to my",
        ]
        if any(s in normalized_text for s in strong_signals):
            # Provide a lightweight hint for future metadata filtering.
            # Extract a title hint after "about"/"on" when present.
            hint = self._extract_knowledge_hint(normalized_text)
            return {"query": normalized_text, "knowledge_hint": hint or ""}
        return None

    def _extract_knowledge_hint(self, normalized_text: str) -> Optional[str]:
        for marker in ["about", "on", "regarding"]:
            if marker in normalized_text:
                return normalized_text.split(marker, 1)[1].strip()
        return None

    def _extract_clipboard_action(self, text: str) -> Optional[str]:
        """Extract a clipboard operation from the input text."""
        if "copy" in text:
            return "copy"
        if "paste" in text:
            return "paste"
        if "clipboard" in text:
            return "show"
        return None

    def _extract_volume_action(self, text: str) -> Optional[str]:
        """Extract a volume operation from the input text."""
        if "mute" in text:
            return "mute"
        if "decrease" in text:
            return "decrease"
        if "increase" in text:
            return "increase"
        return None

    def _extract_brightness_action(self, text: str) -> Optional[str]:
        """Extract a brightness operation from the input text."""
        if "current" in text or "level" in text:
            return "current"
        if "decrease" in text:
            return "decrease"
        if "increase" in text:
            return "increase"
        return None

    def _extract_expression(self, text: str) -> Optional[str]:
        """Extract a calculator expression from the input text."""
        cleaned = text.strip()
        if cleaned.startswith("calculate"):
            return cleaned.replace("calculate", "", 1).strip()
        return cleaned if any(char in cleaned for char in ["+", "-", "*", "/", "%", "(", ")", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]) else None

