import speech_recognition as sr
import logging
from typing import Optional, Callable
from voice_companion.noise_filter import NoiseFilter

logger = logging.getLogger(__name__)

class ContinuousListener:
    """Actively records full sentences to pass to the brain."""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.noise_filter = NoiseFilter(dynamic_energy_threshold=True)
        self.mic = sr.Microphone()
        
        # Calibrate once on startup
        with self.mic as source:
            self.noise_filter.apply(self.recognizer, source, duration=1.5)
            
    def listen_once(self, timeout: int = 5, check_cancelled: Optional[Callable] = None) -> str:
        """Listens for a single phrase and returns the transcribed text."""
        try:
            with self.mic as source:
                logger.info("Listening for speech...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                
            if check_cancelled and check_cancelled():
                return ""
                
            logger.info("Processing speech...")
            text = self.recognizer.recognize_google(audio)
            return text
            
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except Exception as e:
            logger.error(f"Listener error: {e}")
            return ""
