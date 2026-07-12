import time
import pytest
from unittest.mock import patch
from brain.event_bus import event_bus
from brain.intelligence.time_engine import TimeEngine
from memory.manager import MemoryManager
from brain.prediction.engine import PredictionEngine, PredictionContext

# Mock memory backend
mock_data = {}

def mock_load_memory():
    return mock_data

def mock_save_memory(data):
    global mock_data
    mock_data = data

@pytest.fixture(autouse=True)
def setup_memory_mock(monkeypatch):
    global mock_data
    mock_data = {}
    monkeypatch.setattr("memory.manager.load_memory", mock_load_memory)
    monkeypatch.setattr("memory.manager.save_memory", mock_save_memory)

def test_event_bus_publish_subscribe():
    received = []
    def callback(data):
        received.append(data)
        
    event_bus.subscribe("TEST_TOPIC", callback)
    event_bus.publish("TEST_TOPIC", {"msg": "hello"})
    
    time.sleep(0.1)
    
    assert len(received) == 1
    assert received[0]["msg"] == "hello"

def test_time_engine():
    yesterday = TimeEngine.resolve_time("yesterday")
    assert yesterday is not None
    assert TimeEngine.relative_time(yesterday) == "yesterday"
    
    today_morning = TimeEngine.resolve_time("morning")
    assert "morning" in TimeEngine.human_time_description(today_morning)

def test_memory_importance_and_decay():
    manager = MemoryManager()
    manager.remember("test_key", "test_value", category="facts", importance="Medium", confidence=0.9)
    
    val = manager.recall("test_key")
    assert val == "test_value"
    
    mock_data["facts"]["test_key"]["last_accessed"] = time.time() - (65 * 24 * 60 * 60)
    
    val2 = manager.recall("test_key")
    assert val2 == "test_value"
    assert mock_data["facts"]["test_key"]["importance"] == "Low"

def test_prediction_explainability():
    class MockMemoryManager:
        def get_observations(self):
            return {"obs1": {"context": {"text": "weather"}}}
        def record_observation(self, *args):
            pass
            
    engine = PredictionEngine(MockMemoryManager())
    suggestion = engine.observe_and_predict(
        user_input="hello", 
        active_topic=None, 
        recent_turns=[], 
        emo_state={}
    )
    
    assert suggestion is not None
    assert "weather" in suggestion.lower()
