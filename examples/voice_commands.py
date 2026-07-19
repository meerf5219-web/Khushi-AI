"""
examples/voice_commands.py
==========================
Demonstrates how to configure and listen to voice streams, and route
voice inputs into the intent system.
"""

import sys
import os

# Append the parent directory to the path so python can find core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from voice.listener import VoiceListener
    from voice.speaker import speak
    
    print("Initializing Voice Synthesizer...")
    speak("Voice diagnostics active.", block=True)
    
    print("Initializing microphone speech listener stream...")
    listener = VoiceListener()
    
    print("\nListening... Say 'take a screenshot' or 'decrease volume'...")
    # Listen to audio stream and perform STT (Speech-to-Text)
    speech_text = listener.listen_and_convert()
    
    if speech_text:
        print(f"Recognized Speech: '{speech_text}'")
        # In a full flow, you would pass this to the Brain context
        speak(f"You said: {speech_text}", block=True)
    else:
        print("No speech detected or mic is muted.")

except ImportError as e:
    print(f"Error: Unable to import core modules. details: {e}")
except Exception as e:
    print(f"Error during voice simulation: {e}")
