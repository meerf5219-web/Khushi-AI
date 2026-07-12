import os
import tempfile
import pathlib
from memory.companion.engine import CompanionMemoryStore, MemoryRecord

def test_companion_memory_store_delete_record():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = os.path.join(temp_dir, "companion_memory.json")
        store = CompanionMemoryStore(file_name=temp_file)
        
        # Test 1: Dict bucket deletion
        record = MemoryRecord(
            created_date="2026-07-10T12:00:00Z",
            updated_date="2026-07-10T12:00:00Z",
            confidence=1.0,
            source="user",
            category="goals",
            payload={"value": "Crack UPSC", "id": "goals:upsc"}
        )
        store.upsert_record(bucket="goals", record_id="goals:upsc", record=record)
        
        # Assert inserted
        summary = store.get_summary()
        assert "goals:upsc" in summary["goals"]["records"]
        
        # Delete record
        deleted = store.delete_record("goals", "goals:upsc")
        assert deleted is True
        
        # Assert deleted
        summary = store.get_summary()
        assert "goals:upsc" not in summary["goals"]["records"]
        
        # Test 2: List bucket (timeline) deletion
        event = {
            "created_at": "2026-07-10T12:00:00Z",
            "category": "goals",
            "memory_id": "goals:upsc",
            "value": "Crack UPSC"
        }
        store.append_event(bucket="timeline", event=event)
        
        # Assert inserted
        summary = store.get_summary()
        assert len(summary["timeline"]["records"]) == 1
        
        # Delete from timeline using memory_id
        deleted = store.delete_record("timeline", "goals:upsc")
        assert deleted is True
        
        # Assert deleted
        summary = store.get_summary()
        assert len(summary["timeline"]["records"]) == 0
