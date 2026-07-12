import sqlite3
import json
import logging
import uuid
import time
import os
from typing import Any, Dict, List, Optional
from brain.event_store.interfaces import EventStore
logger = logging.getLogger(__name__)

class SQLiteEventStore(EventStore):
    def __init__(self, db_path: str = None):
        if db_path is None:
            from utils.paths import get_data_dir
            db_path = str(get_data_dir() / "memory" / "raw_events.db")
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    timestamp REAL,
                    session_id TEXT,
                    conversation_id TEXT,
                    source TEXT,
                    speaker TEXT,
                    raw_text TEXT,
                    normalized_text TEXT,
                    intent TEXT,
                    confidence REAL,
                    entities TEXT,
                    emotion TEXT,
                    metadata TEXT,
                    processed INTEGER DEFAULT 0,
                    schema_version INTEGER DEFAULT 1
                )
            ''')
            # Indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_intent ON events(intent)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON events(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversation_id ON events(conversation_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON events(source)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_speaker ON events(speaker)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_processed ON events(processed)')
            conn.commit()

    def _generate_id(self) -> str:
        # Fallback to UUID4 if UUID7 is not natively in python's uuid module
        return str(uuid.uuid4())

    def append_event(self, event_data: Dict[str, Any]) -> str:
        event_id = event_data.get("event_id") or self._generate_id()
        timestamp = event_data.get("timestamp", time.time())
        session_id = event_data.get("session_id", "")
        conversation_id = event_data.get("conversation_id", "")
        source = event_data.get("source", "user")
        speaker = event_data.get("speaker", "user")
        raw_text = event_data.get("raw_text", "")
        normalized_text = event_data.get("normalized_text", "")
        intent = event_data.get("intent", "")
        confidence = event_data.get("confidence", 0.0)
        entities = json.dumps(event_data.get("entities", {}))
        emotion = json.dumps(event_data.get("emotion", {}))
        metadata = json.dumps(event_data.get("metadata", {}))
        processed = 1 if event_data.get("processed") else 0
        schema_version = event_data.get("schema_version", 1)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO events (
                        event_id, timestamp, session_id, conversation_id, source, speaker,
                        raw_text, normalized_text, intent, confidence, entities, emotion,
                        metadata, processed, schema_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (event_id, timestamp, session_id, conversation_id, source, speaker,
                      raw_text, normalized_text, intent, confidence, entities, emotion,
                      metadata, processed, schema_version))
                conn.commit()
                logger.info("RAW_SAVED: Event %s saved successfully", event_id)
                logger.info("EVENT_INDEXED: Event %s indexed", event_id)
            except sqlite3.IntegrityError:
                # Event already exists or conflict
                logger.error("Failed to append event %s: IntegrityError", event_id)
                raise
        return event_id

    def get_unprocessed_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM events WHERE processed = 0 ORDER BY timestamp ASC LIMIT ?', (limit,))
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

    def mark_processed(self, event_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE events SET processed = 1 WHERE event_id = ?', (event_id,))
            conn.commit()
            logger.info("EVENT_PROCESSED: Event %s marked as processed", event_id)

    def get_all_events(self, batch_size: int = 1000):
        """Generator that yields batches of events for replay."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM events ORDER BY timestamp ASC')
            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                yield [self._row_to_dict(row) for row in rows]

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        d['entities'] = json.loads(d['entities']) if d['entities'] else {}
        d['emotion'] = json.loads(d['emotion']) if d['emotion'] else {}
        d['metadata'] = json.loads(d['metadata']) if d['metadata'] else {}
        d['processed'] = bool(d['processed'])
        return d
