import pytest
from unittest.mock import patch, MagicMock
import time

@pytest.fixture
def router():
    from voice_companion.speech_router import SpeechRouter
    return SpeechRouter(brain=MagicMock())

def test_wakeword_switches_mode(router):
    """Test that detecting a wakeword switches from dormant to listening."""
    with patch('voice_companion.wakeword.WakeWordDetector.start') as mock_start:
        router.start_service()
        mock_start.assert_called_once()
        
    with patch('voice_companion.speech_router.SpeechRouter._start_listening_session') as mock_listen:
        router._on_wakeword_detected()
        mock_listen.assert_called_once()

@patch('voice_companion.stream_tts.pyttsx3.init')
def test_interrupt_halts_tts(mock_init, router):
    """Test that a user interrupt instantly halts TTS."""
    router.tts.start()
    
    # Simulate adding TTS
    router.tts.speak_chunk("Hello")
    router.tts.speak_chunk("World")
    
    assert not router.tts.queue.empty()
    
    # Trigger interrupt
    router._on_user_interrupted()
    
    # Queue should be cleared instantly
    assert router.tts.queue.empty()
    assert router.tts.stop_event.is_set()

def test_streaming_first_token_latency(router):
    """Ensure pseudo-streaming chunks sentences without blocking the caller."""
    router.tts.start()
    
    start_time = time.time()
    router.tts.speak_chunk("This is a quick sentence.")
    end_time = time.time()
    
    # Adding to queue should be instantaneous (<< 150ms)
    assert (end_time - start_time) < 0.150
