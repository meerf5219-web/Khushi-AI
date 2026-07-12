import logging
import os
from typing import Any
from brain.event_store.interfaces import EventStore
from brain.event_store.processor import EventProcessor

logger = logging.getLogger(__name__)

class EventReplayer:
    def __init__(self, event_store: EventStore, processor: EventProcessor, memory_manager: Any):
        self.store = event_store
        self.processor = processor
        self.memory = memory_manager

    def replay_all(self, batch_size: int = 1000) -> None:
        """Manual Replay: Wipe memory and rebuild from raw events deterministically."""
        logger.info("EVENT_REPLAY_STARTED")
        try:
            self._wipe_memory()
            
            for batch in self.store.get_all_events(batch_size=batch_size):
                for event in batch:
                    self.processor._process_single(event)
            
            logger.info("EVENT_REPLAY_COMPLETED")
        except Exception as e:
            logger.error("EVENT_REPLAY_FAILED: %s", str(e))
            raise

    def _wipe_memory(self) -> None:
        """Truncate all current derived memories."""
        from memory.memory import save_memory, FILE_NAME, OLD_FILE_NAME
        if os.path.exists(FILE_NAME):
            os.remove(FILE_NAME)
        if os.path.exists(OLD_FILE_NAME):
            os.remove(OLD_FILE_NAME)
        save_memory({})

    def auto_recover(self, force: bool = False) -> None:
        """Automatic Recovery on startup."""
        from memory.memory import FILE_NAME, OLD_FILE_NAME, load_memory
        
        needs_recovery = force
        if not os.path.exists(FILE_NAME) and not os.path.exists(OLD_FILE_NAME):
            needs_recovery = True
        else:
            data = load_memory()
            if not data:
                needs_recovery = True
            elif data.get("_schema_version", 1) < 1:
                needs_recovery = True
                
        if needs_recovery:
            logger.warning("Triggering Automatic Event Replay Recovery")
            self.replay_all()
