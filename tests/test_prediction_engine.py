import pytest
from brain.prediction.engine import PredictionEngine

class MockMemoryManager:
    def __init__(self):
        self.observations = {}

    def record_observation(self, event_type, context):
        import uuid
        import time
        obs_id = f"obs_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        self.observations[obs_id] = {
            "type": event_type,
            "timestamp": time.time(),
            "context": context
        }

    def get_observations(self):
        return self.observations

def test_prediction_engine_observe():
    memory = MockMemoryManager()
    engine = PredictionEngine(memory)
    engine.observe_and_predict(
        user_input="hello", 
        active_topic=None, 
        recent_turns=[], 
        emo_state={}
    )
    obs = memory.get_observations()
    assert len(obs) == 1
    obs_list = list(obs.values())
    assert obs_list[0]["type"] == "user_input"
    assert obs_list[0]["context"]["text"] == "hello"

def test_prediction_engine_suggest():
    memory = MockMemoryManager()
    engine = PredictionEngine(memory)
    # Simulate user checking weather multiple times
    engine.observe_and_predict("weather in london", None, [], {})
    engine.observe_and_predict("weather today", None, [], {})
    
    # On next turn, without saying weather, it should predict weather based on observation pattern
    suggestion = engine.observe_and_predict("good morning", None, [], {})
    assert suggestion is not None
    assert "weather" in suggestion.lower()
    
    # Check if explainability logic added "pattern" or "recently"
    assert "pattern" in suggestion.lower() or "recently" in suggestion.lower()
