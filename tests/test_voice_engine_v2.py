import os
import wave
import struct
import tempfile
import pytest
from voice.voice_engine import VoiceEngineV2

@pytest.fixture
def voice_engine():
    # Use dummy mode for fast, deterministic unit testing
    return VoiceEngineV2(use_pyttsx3=False)

def test_pronunciation_dictionary(voice_engine):
    # Test default dictionary
    text = "Study for UPSC and JKPSC exams using RAG with ChromaDB and FAISS in Python on GitHub."
    processed = voice_engine.apply_pronunciation(text)
    assert "U P S C" in processed
    assert "J K P S C" in processed
    assert "R A G" in processed
    assert "Chroma D B" in processed
    assert "Fase" in processed
    assert "Python" in processed
    assert "Git Hub" in processed

    # Test custom dynamic pronunciation
    voice_engine.add_custom_pronunciation("AI", "A I")
    assert voice_engine.apply_pronunciation("Learn AI") == "Learn A I"

def test_breathing_model(voice_engine):
    # Short text should not trigger breathing model
    short_text = "This is short."
    assert voice_engine.apply_breathing(short_text) == short_text

    # Long text with conjunctions should have breathing pauses inserted
    long_text = "Learning the Indian Constitution is important because it is the supreme law of India and it provides the framework for governance."
    processed = voice_engine.apply_breathing(long_text)
    assert ", because" in processed

def test_prosody(voice_engine):
    # Verify question mark is kept or appended
    assert voice_engine.apply_prosody("What is UPSC", True) == "What is UPSC?"
    assert voice_engine.apply_prosody("What is UPSC?", True) == "What is UPSC?"
    assert voice_engine.apply_prosody("This is a statement.", False) == "This is a statement."

def test_volume_capping(voice_engine):
    # Verify volume is capped at 1.0
    metrics = voice_engine.speak_action("Hello", rate=150, volume=1.5, profile="Professional", style="Professional")
    assert len(voice_engine.performance_logs) > 0
    assert voice_engine.performance_logs[-1]["processed_text"] == "Hello"

def test_wav_normalization(voice_engine):
    # Create a temporary dummy WAV file
    temp_dir = tempfile.gettempdir()
    temp_wav = os.path.join(temp_dir, "test_normalize.wav")
    
    # Write a 1-second 16-bit mono 22050Hz silent/low-amplitude WAV file
    sample_rate = 22050
    duration = 0.5
    num_samples = int(sample_rate * duration)
    
    # Low amplitude samples (max peak is 1000)
    samples = [1000 if i % 2 == 0 else -1000 for i in range(num_samples)]
    packed_data = struct.pack(f"<{num_samples}h", *samples)
    
    with wave.open(temp_wav, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(packed_data)
        
    try:
        # Run normalization
        voice_engine._normalize_wav(temp_wav)
        
        # Read normalized file back
        with wave.open(temp_wav, "rb") as w:
            frames = w.readframes(num_samples)
            
        normalized_samples = list(struct.unpack(f"<{num_samples}h", frames))
        # The peak should now be normalized to 29491
        max_val = max(abs(s) for s in normalized_samples)
        assert abs(max_val - 29491) < 10 # very close to target peak
        
        # Check that fade-in is applied (the first few samples should be scaled down relative to the peak)
        assert abs(normalized_samples[0]) == 0
        assert abs(normalized_samples[10]) < 5000
    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)

def test_performance_metrics(voice_engine):
    voice_engine.performance_logs.clear()
    metrics = voice_engine.speak_action("Test performance metrics.", rate=165, volume=1.0, profile="Teaching", style="Calm")
    assert "generation_time" in metrics
    assert "playback_latency" in metrics
    assert "total_time" in metrics
    assert len(voice_engine.performance_logs) == 1
