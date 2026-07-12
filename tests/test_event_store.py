import os
import time
import pytest
import sqlite3
import threading
from brain.event_store.sqlite_store import SQLiteEventStore
from brain.event_store.processor import EventProcessor
from brain.event_store.replayer import EventReplayer

class MockMemoryManager:
    def __init__(self):
        self.observations = {}
        self.memories = {}

    def record_observation(self, event_type, context):
        obs_id = f"obs_{len(self.observations)}"
        self.observations[obs_id] = {"type": event_type, "context": context}

    def remember(self, key, value, category="facts"):
        if category not in self.memories:
            self.memories[category] = {}
        self.memories[category][key] = value

@pytest.fixture
def temp_db(tmp_path):
    db_path = os.path.join(tmp_path, "test_events.db")
    return db_path

def test_event_append_only(temp_db):
    store = SQLiteEventStore(db_path=temp_db)
    event_id = store.append_event({"raw_text": "hello", "processed": 0})
    
    # Try to overwrite
    with pytest.raises(sqlite3.IntegrityError):
        store.append_event({"event_id": event_id, "raw_text": "world"})
        
    # Check it wasn't modified
    unprocessed = store.get_unprocessed_events()
    assert len(unprocessed) == 1
    assert unprocessed[0]["raw_text"] == "hello"

def test_immutable_raw_events(temp_db):
    store = SQLiteEventStore(db_path=temp_db)
    memory = MockMemoryManager()
    processor = EventProcessor(store, memory)
    
    event_id = store.append_event({"raw_text": "hello world"})
    processor.process_pending()
    
    # Check that it's processed
    unprocessed = store.get_unprocessed_events()
    assert len(unprocessed) == 0
    
    # Check that raw text is immutable
    with sqlite3.connect(temp_db) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE event_id = ?", (event_id,))
        row = cursor.fetchone()
        assert row["raw_text"] == "hello world"
        assert row["processed"] == 1

def test_replay_determinism(temp_db):
    store = SQLiteEventStore(db_path=temp_db)
    memory = MockMemoryManager()
    processor = EventProcessor(store, memory)
    replayer = EventReplayer(store, processor, memory)
    
    store.append_event({"raw_text": "i live in london", "normalized_text": "i live in london"})
    store.append_event({"raw_text": "how's the weather", "normalized_text": "weather"})
    
    processor.process_pending()
    assert memory.memories.get("personal", {}).get("location") == "london"
    assert len(memory.observations) == 2
    
    # Save state
    initial_observations = len(memory.observations)
    initial_location = memory.memories.get("personal", {}).get("location")
    
    # Clear memory (mock wiping)
    memory.observations = {}
    memory.memories = {}
    
    # Replay
    replayer._wipe_memory = lambda: None
    replayer.replay_all(batch_size=1)
    
    assert len(memory.observations) == initial_observations
    assert memory.memories.get("personal", {}).get("location") == initial_location

def test_large_event_log(temp_db):
    store = SQLiteEventStore(db_path=temp_db)
    
    # Insert 10k simulated events via direct executemany for speed
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute('BEGIN TRANSACTION')
        events = [(f"e_{i}", time.time(), f"text {i}") for i in range(10000)]
        cursor.executemany("INSERT INTO events (event_id, timestamp, raw_text) VALUES (?, ?, ?)", events)
        conn.commit()
        
    memory = MockMemoryManager()
    processor = EventProcessor(store, memory)
    replayer = EventReplayer(store, processor, memory)
    replayer._wipe_memory = lambda: None
    
    t1 = time.time()
    replayer.replay_all(batch_size=1000)
    t2 = time.time()
    
    assert len(memory.observations) == 10000
    assert (t2 - t1) < 10.0  # Should process 10k events quickly

def test_concurrent_reads(temp_db):
    store = SQLiteEventStore(db_path=temp_db)
    store.append_event({"raw_text": "test"})
    
    def read_worker():
        s = SQLiteEventStore(db_path=temp_db)
        events = s.get_unprocessed_events()
        assert len(events) >= 0

    threads = [threading.Thread(target=read_worker) for _ in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()
