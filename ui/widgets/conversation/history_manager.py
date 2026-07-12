"""
ui/widgets/conversation/history_manager.py — Local SQLite History virtualization manager
==========================================================================================
Manages conversation logs stored in SQLite EventStore. Performs lazy-loading (pagination)
to support 100,000+ turns without causing UI freezes or excessive RAM allocations.
"""
from __future__ import annotations

import sqlite3
import json
import logging
from typing import Any, Dict, List, Tuple
from brain.event_store.sqlite_store import SQLiteEventStore

logger = logging.getLogger(__name__)


class HistoryManager:
    """
    Manages lazy loading and formatting of user and assistant conversation history.
    """

    def __init__(self, db_path: str = None) -> None:
        self.store = SQLiteEventStore(db_path)
        logger.info("[HISTORY MANAGER] Connected to SQLite database at: %s", self.store.db_path)

    def load_recent_turns(self, offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Lazily fetch historical dialogue records from events table, ordered descending by timestamp.
        Combines User and Assistant entries into structured turn dictionaries.
        """
        turns: List[Dict[str, Any]] = []
        try:
            with sqlite3.connect(self.store.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                # Query user inputs and assistant responses
                # Order by timestamp desc to lazy load backwards
                cursor.execute("""
                    SELECT * FROM events 
                    ORDER BY timestamp DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                rows = cursor.fetchall()
                for row in rows:
                    metadata_dict = {}
                    try:
                        metadata_dict = json.loads(row["metadata"]) if row["metadata"] else {}
                    except Exception:
                        pass
                    
                    turns.append({
                        "event_id": row["event_id"],
                        "timestamp": row["timestamp"],
                        "source": row["source"],
                        "speaker": row["speaker"],
                        "raw_text": row["raw_text"],
                        "intent": row["intent"],
                        "metadata": metadata_dict
                    })
            # Reverse order before returning so they appear chronologically inside UI layouts
            turns.reverse()
        except Exception as exc:
            logger.error("[HISTORY MANAGER] Failed to load history: %s", exc)
        return turns

    def save_turn(self, sender: str, text: str, intent: str = "", metadata: Dict[str, Any] = None) -> str:
        """
        Write a single user query or assistant reply directly into the event store.
        """
        event = {
            "source": sender,
            "speaker": "user" if sender == "user" else "Khushi",
            "raw_text": text,
            "normalized_text": text,
            "intent": intent,
            "metadata": metadata or {},
            "processed": 1
        }
        return self.store.append_event(event)

    def edit_last_user_event(self, text: str) -> None:
        """
        Finds the very last user message in the database and updates its text content.
        Useful when editing the last message to re-run Brain logic.
        """
        try:
            with sqlite3.connect(self.store.db_path) as conn:
                cursor = conn.cursor()
                # Find last user event
                cursor.execute("""
                    SELECT event_id FROM events 
                    WHERE source = 'user' 
                    ORDER BY timestamp DESC LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    last_id = row[0]
                    cursor.execute("""
                        UPDATE events 
                        SET raw_text = ?, normalized_text = ? 
                        WHERE event_id = ?
                    """, (text, text, last_id))
                    conn.commit()
                    logger.info("[HISTORY MANAGER] Updated last user event %s text to: '%s'", last_id, text[:40])
        except Exception as exc:
            logger.error("[HISTORY MANAGER] Failed to edit last user event: %s", exc)

    def delete_message(self, event_id: str) -> bool:
        """
        Delete a message from history.
        """
        try:
            with sqlite3.connect(self.store.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM events WHERE event_id = ?", (event_id,))
                conn.commit()
                logger.info("[HISTORY MANAGER] Deleted event: %s", event_id)
                return True
        except Exception as exc:
            logger.error("[HISTORY MANAGER] Failed to delete event %s: %s", event_id, exc)
            return False
