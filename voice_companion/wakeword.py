import speech_recognition as sr
import logging
from typing import Callable, List, Optional
from voice_companion.noise_filter import NoiseFilter

logger = logging.getLogger(__name__)

class WakeWordDetector:
    """Continuously listens for a specific hotword."""
    
    def __init__(self, wake_words: List[str] = ["hey khushi", "khushi"]):
        self.wake_words = [w.lower() for w in wake_words]
        self.recognizer = sr.Recognizer()
        self.noise_filter = NoiseFilter()
        self._stop_listening_func: Optional[Callable] = None
        
    def start(self, on_detected: Callable):
        """Starts background listening for the wake word."""
        if self._stop_listening_func:
            return # Already running
            
        mic = sr.Microphone()
        with mic as source:
            self.noise_filter.apply(self.recognizer, source, duration=1.0)
            
        logger.info(f"Started listening for wake words: {self.wake_words}")
        
        def callback(recognizer, audio):
            try:
                # Use fast, offline Sphinx if possible, else fallback to google
                text = recognizer.recognize_google(audio).lower()
                if any(ww in text for ww in self.wake_words):
                    logger.info(f"Wake word detected in phrase: '{text}'")
                    on_detected()
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                logger.error(f"Could not request results from speech recognition service; {e}")
                
        # listen_in_background spawns its own thread and returns a stop function
        self._stop_listening_func = self.recognizer.listen_in_background(mic, callback, phrase_time_limit=3)
        
    def stop(self):
        if self._stop_listening_func:
            self._stop_listening_func(wait_for_stop=False)
            self._stop_listening_func = None
            logger.info("Stopped wake word detector.")
