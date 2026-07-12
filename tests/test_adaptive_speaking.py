import time
import pytest
from brain.speaking_engine.engine import (
    AdaptiveSpeakingEngine,
    SpeechAction,
    SpeechRequest,
    RATE_FAST,
    RATE_MODERATE,
    RATE_SLOW,
)

@pytest.fixture
def speaking_engine():
    # Use dummy mode for fast, deterministic unit testing
    engine = AdaptiveSpeakingEngine(use_pyttsx3=False, sleep_multiplier=0.2)
    return engine

def test_detect_profile(speaking_engine):
    assert speaking_engine.detect_profile("Here is some code: ```python def foo(): pass```") == "Coding"
    assert speaking_engine.detect_profile("This is a warning! Please be careful.") == "Warnings"
    assert speaking_engine.detect_profile("An error occurred: connection timed out.") == "Error Messages"
    assert speaking_engine.detect_profile("Task completed successfully. Test passed!") == "Success Messages"
    assert speaking_engine.detect_profile("Let me explain how this works in this tutorial.") == "Teaching"
    assert speaking_engine.detect_profile("Keep going, I am proud of you!") == "Motivation"
    assert speaking_engine.detect_profile("Hello, how is the weather today?") == "General Chat"

def test_calculate_pacing(speaking_engine):
    # Short answer (< 60 chars) should be faster
    short_rate = speaking_engine.calculate_pacing("Yes, done.", "General Chat")
    assert short_rate > RATE_MODERATE

    # Long answer (> 200 chars) should be slower/moderate
    long_text = "This is a very long explanation about a complex topic that contains many words and is intended to test if the speaking engine will adjust its rate down to a moderate pace for readability."
    long_rate = speaking_engine.calculate_pacing(long_text, "General Chat")
    assert long_rate < short_rate

    # Warnings profile should be slow
    warning_rate = speaking_engine.calculate_pacing("Warning", "Warnings")
    assert warning_rate < RATE_MODERATE

def test_natural_pauses(speaking_engine):
    # Test paragraph pause (0.6s)
    text_para = "First paragraph.\n\nSecond paragraph."
    actions = speaking_engine.parse_actions(text_para, "General Chat", "Professional")
    pauses = [a.duration for a in actions if a.action_type == "pause"]
    assert 0.6 in pauses

    # Test list pause (0.4s)
    text_list = "- First item\n- Second item"
    actions_list = speaking_engine.parse_actions(text_list, "General Chat", "Professional")
    pauses_list = [a.duration for a in actions_list if a.action_type == "pause"]
    assert 0.4 in pauses_list

    # Test question pause (0.3s)
    text_quest = "How are you? I am fine."
    actions_quest = speaking_engine.parse_actions(text_quest, "General Chat", "Professional")
    pauses_quest = [a.duration for a in actions_quest if a.action_type == "pause"]
    assert 0.3 in pauses_quest

    # Test clause pause (0.2s)
    text_clause = "This is important; please listen."
    actions_clause = speaking_engine.parse_actions(text_clause, "General Chat", "Professional")
    pauses_clause = [a.duration for a in actions_clause if a.action_type == "pause"]
    assert 0.2 in pauses_clause

def test_emphasis_engine(speaking_engine):
    # Test date, deadline, number, and goal emphasis
    text = "The deadline is July 8 for the UPSC goal. We need 100% success."
    actions = speaking_engine.parse_actions(text, "General Chat", "Professional")
    
    # Check that some chunks are marked with emphasis
    emphasized = [a for a in actions if a.action_type == "speak" and a.emphasis]
    assert len(emphasized) > 0
    
    # Emphasized chunks should have lower rate
    emphasized_words = [a.text.lower() for a in emphasized]
    for w in ["deadline", "july 8", "upsc"]:
        assert any(w in emp_word for emp_word in emphasized_words)

def test_queue_and_cancellation(speaking_engine):
    speaking_engine.cancel()
    
    # Queue three items, but the later ones cancel previous
    speaking_engine.speak("First response", cancel_previous=False)
    speaking_engine.speak("Second response", cancel_previous=False)
    
    # Give the thread a tiny bit of time to queue/start
    time.sleep(0.1)
    
    # There should be items or active requests
    assert speaking_engine.is_playing or not speaking_engine.queue.empty()
    
    # Cancel previous should drain queue and stop
    req3 = speaking_engine.speak("Third response", cancel_previous=True)
    time.sleep(0.1)
    
    # Queue should be drained of previous, third should run or complete
    assert req3.completed_event.wait(timeout=2.0)
    
def test_interruption_controls(speaking_engine):
    speaking_engine.cancel()
    
    # Pause the engine
    speaking_engine.pause()
    assert speaking_engine.is_paused
    
    req = speaking_engine.speak("This is a paused speech item.", cancel_previous=True, block=False)
    time.sleep(0.1)
    
    # Request should not be complete because it's paused
    assert not req.completed_event.is_set()
    
    # Resume
    speaking_engine.resume()
    assert not speaking_engine.is_paused
    
    # Should complete shortly after resuming
    assert req.completed_event.wait(timeout=2.0)

def test_streaming_speech(speaking_engine):
    speaking_engine.cancel()
    
    def chunk_generator():
        yield "Starting "
        yield "the stream. "
        yield "This is a sentence. "
        yield "And another one."
        
    req = speaking_engine.speak_stream(chunk_generator(), cancel_previous=True, block=True)
    assert req.completed_event.is_set()
    assert req.end_time is not None
    assert len(speaking_engine.performance_logs) > 0

def test_performance_logs(speaking_engine):
    speaking_engine.cancel()
    req = speaking_engine.speak("Short test for latency logs.", cancel_previous=True, block=True)
    
    logs = speaking_engine.get_performance_logs()
    assert len(logs) > 0
    last_log = logs[-1]
    assert last_log["request_id"] == req.request_id
    assert "speech_latency" in last_log
    assert "total_response_latency" in last_log
    assert "queue_time" in last_log
