import logging
import time
from typing import Any, Dict
from brain.event_store.interfaces import EventStore

logger = logging.getLogger(__name__)

class EventProcessor:
    def __init__(self, event_store: EventStore, memory_manager: Any):
        self.store = event_store
        self.memory = memory_manager

    def process_pending(self) -> None:
        events = self.store.get_unprocessed_events(limit=100)
        for event in events:
            self._process_single(event)
            self.store.mark_processed(event["event_id"])

    def _process_single(self, event: Dict[str, Any]) -> None:
        """Derive information from raw event without modifying the raw event."""
        # 1. Observation records (for Predictions)
        if event.get("raw_text"):
            self.memory.record_observation("user_input", {
                "text": event.get("raw_text"),
                "topic": event.get("metadata", {}).get("topic"),
                "hour": time.localtime(event.get("timestamp", time.time())).tm_hour
            })

        # 2. Semantic Memory
        # Extract explicit facts if present (mocked logic for integration)
        normalized = (event.get("normalized_text") or "").lower()
        if normalized.startswith("i live in "):
            location = normalized.replace("i live in ", "").strip()
            self.memory.remember("location", location, category="personal")

        # 3. Companion Memory & Timeline
        # Log to companion interaction history
        pass

        # 4. Predictions
        # Update prediction models if necessary
        pass
        
        # 5. Knowledge Updates
        pass
