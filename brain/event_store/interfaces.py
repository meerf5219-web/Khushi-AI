from abc import ABC, abstractmethod
from typing import Any, Dict, List

class EventStore(ABC):
    @abstractmethod
    def append_event(self, event_data: Dict[str, Any]) -> str:
        """Append a new immutable event. Returns the event_id."""
        pass

    @abstractmethod
    def get_unprocessed_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch a batch of unprocessed events."""
        pass

    @abstractmethod
    def mark_processed(self, event_id: str) -> None:
        """Mark an event as processed. The only mutable operation allowed."""
        pass

    @abstractmethod
    def get_all_events(self, batch_size: int = 1000):
        """Generator that yields batches of all events for replay."""
        pass
