import logging
import re
import time
import uuid
from typing import Any, Dict, Optional

from memory.memory import load_memory, save_memory

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manage contextual, category-aware long-term memory."""

    MEMORY_CATEGORIES = {"personal", "preferences", "facts", "notes", "tasks", "observations", "patterns"}

    def __init__(self, brain=None) -> None:
        self.brain = brain

    def record_observation(self, event_type: str, context: Dict[str, Any]) -> None:
        """Record an observation event for the Predictive Companion (Generation 2)."""
        obs_id = f"obs_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        observation = {
            "type": event_type,
            "timestamp": time.time(),
            "context": context
        }
        
        data = load_memory()
        category_key = "observations"
        if category_key not in data:
            data[category_key] = {}
            
        data[category_key][obs_id] = observation
        save_memory(data)
        logger.info("Recorded observation: %s -> %s", event_type, obs_id)

    def get_observations(self) -> Dict[str, Any]:
        """Retrieve all recorded observations."""
        data = load_memory()
        return data.get("observations", {})

    def remember(self, key: str, value: str, category: str = "facts", importance: str = "Medium", confidence: float = 1.0) -> None:
        """Store a value in persistent memory under a category with metadata."""
        data = load_memory()
        category_key = self._normalize_category(category)
        if category_key not in data:
            data[category_key] = {}

        memory_obj = {
            "value": value,
            "importance": importance,
            "confidence": confidence,
            "last_accessed": time.time(),
            "created_at": time.time(),
            "updated_at": time.time()
        }

        data[category_key][self._normalize_key(key)] = memory_obj
        save_memory(data)
        logger.info("Saved memory: %s -> %s in %s", key, value, category_key)
        
        if self.brain and hasattr(self.brain, "world") and self.brain.world:
            conflict = self.brain.world.check_conflict(label=category_key, name=key, value=value)
            if conflict:
                logger.warning(f"Memory conflict: {conflict['message']}")
                try:
                    from brain.event_bus import event_bus
                    event_bus.publish("MEMORY_CONFLICT", conflict)
                except Exception:
                    pass
            self.brain.world.merge_memory(label=category_key, name=key, metadata={"value": value, "importance": importance})

        try:
            from brain.event_bus import event_bus
            event_bus.publish("MEMORY_UPDATED", {"key": key, "category": category, "importance": importance})
        except ImportError:
            pass

    def recall(self, key: str) -> Optional[Any]:
        """Retrieve a value from persistent memory across categories."""
        data = load_memory()
        for category in self.MEMORY_CATEGORIES:
            cat_data = data.get(category)
            if isinstance(cat_data, dict):
                norm_key = self._normalize_key(key)
                if norm_key in cat_data:
                    val = cat_data[norm_key]
                    
                    # Auto-upgrade legacy string memory
                    if isinstance(val, str):
                        val = {
                            "value": val,
                            "importance": "Medium",
                            "confidence": 1.0,
                            "last_accessed": time.time(),
                            "created_at": time.time(),
                            "updated_at": time.time()
                        }
                    
                    # Apply decay logic
                    val = self._apply_decay(val)
                    
                    # Update last accessed
                    val["last_accessed"] = time.time()
                    cat_data[norm_key] = val
                    save_memory(data)
                    
                    logger.info("Recalled memory for key: %s (Importance: %s)", key, val.get("importance"))
                    return val["value"]

        logger.info("No memory found for key: %s", key)
        return None

    def _apply_decay(self, memory_obj: Dict[str, Any]) -> Dict[str, Any]:
        """Downgrade importance based on time elapsed since last access."""
        importance = memory_obj.get("importance", "Medium")
        if importance == "Critical":
            return memory_obj
            
        last_accessed = memory_obj.get("last_accessed", time.time())
        days_elapsed = (time.time() - last_accessed) / (60 * 60 * 24)
        
        if days_elapsed > 30 and importance == "High":
            memory_obj["importance"] = "Medium"
        elif days_elapsed > 60 and importance == "Medium":
            memory_obj["importance"] = "Low"
        elif days_elapsed > 90 and importance == "Low":
            memory_obj["importance"] = "Archived"
            
        return memory_obj

    def save_statement(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse a natural-language statement and save it as structured memory."""
        normalized_text = text.strip()
        if not normalized_text:
            return None

        if normalized_text.lower().startswith("my favourite"):
            key, value = self._parse_preference_statement(normalized_text)
            if key and value:
                self.remember(key, value, category="preferences")
                return {"category": "preferences", "key": key, "value": value}

        if normalized_text.lower().startswith("i live in"):
            location = normalized_text.replace("i live in", "", 1).strip()
            self.remember("location", location, category="personal")
            return {"category": "personal", "key": "location", "value": location}

        if normalized_text.lower().startswith("i study"):
            subject = normalized_text.replace("i study", "", 1).strip()
            self.remember("study", subject, category="facts")
            return {"category": "facts", "key": "study", "value": subject}

        if normalized_text.lower().startswith("i am") and "years old" in normalized_text.lower():
            age = normalized_text.replace("i am", "", 1).replace("years old", "", 1).strip()
            self.remember("age", age, category="personal")
            return {"category": "personal", "key": "age", "value": age}

        return None

    def recall_question(self, text: str) -> Optional[str]:
        """Answer a natural-language recall question using stored memory."""
        normalized_text = text.lower().strip()
        if "favourite" in normalized_text or "favorite" in normalized_text:
            key = self._extract_preference_key(normalized_text)
            if key:
                value = self.recall(key)
                if value is not None:
                    return f"Your {key.replace('_', ' ')} is {value}."

        if "live" in normalized_text or "where do i live" in normalized_text:
            value = self.recall("location")
            if value is not None:
                return f"You live in {value}."

        if "study" in normalized_text:
            value = self.recall("study")
            if value is not None:
                return f"You study {value}."

        if "old" in normalized_text or "age" in normalized_text:
            value = self.recall("age")
            if value is not None:
                return f"You are {value} years old."

        return None

    def _parse_preference_statement(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """Parse a preference statement like 'My favourite colour is black'."""
        match = re.match(r"my favourite(?: colour| color)?\s+(.+?)\s+is\s+(.+)", text, re.IGNORECASE)
        if not match:
            return None, None

        trait = match.group(1).strip()
        value = match.group(2).strip()
        key = self._normalize_key(f"favourite_{trait}")
        return key, value

    def _extract_preference_key(self, text: str) -> Optional[str]:
        """Extract the preference key from a question such as 'What is my favourite colour?'"""
        for word in ["colour", "color", "food", "car"]:
            if word in text:
                return self._normalize_key(f"favourite_{word}")
        return None

    def _normalize_category(self, category: str) -> str:
        """Normalize a category name to the supported memory category list."""
        normalized = category.lower().strip()
        return normalized if normalized in self.MEMORY_CATEGORIES else "facts"

    def _normalize_key(self, key: str) -> str:
        """Normalize a key into a predictable snake_case format."""
        key = key.strip().lower()
        key = re.sub(r"[^a-z0-9]+", "_", key)
        return key.strip("_")