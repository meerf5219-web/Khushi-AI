import logging
import threading
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)

class EventBus:
    """Internal Event Bus for loose coupling and publish/subscribe."""
    
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EventBus, cls).__new__(cls)
                cls._instance._subscribers = {}
                cls._instance._bus_lock = threading.Lock()
        return cls._instance

    def subscribe(self, topic: str, callback: Callable[[Any], None]) -> None:
        """Subscribe to a topic."""
        with self._bus_lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            if callback not in self._subscribers[topic]:
                self._subscribers[topic].append(callback)
            logger.debug(f"Subscribed to topic '{topic}'")

    def unsubscribe(self, topic: str, callback: Callable[[Any], None]) -> None:
        """Unsubscribe a callback from a topic."""
        with self._bus_lock:
            if topic in self._subscribers and callback in self._subscribers[topic]:
                self._subscribers[topic].remove(callback)
                logger.debug(f"Unsubscribed from topic '{topic}'")

    def publish(self, topic: str, data: Any) -> None:
        """Publish data to a topic asynchronously to avoid blocking."""
        with self._bus_lock:
            callbacks = self._subscribers.get(topic, []).copy()

        if not callbacks:
            return

        def _notify():
            for callback in callbacks:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in EventBus subscriber for topic '{topic}': {e}", exc_info=True)

        # Execute in a new thread for async safety
        thread = threading.Thread(target=_notify, daemon=True)
        thread.start()

# Global instance for easy import
event_bus = EventBus()
