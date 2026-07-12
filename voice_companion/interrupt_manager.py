import logging
import speech_recognition as sr
from typing import Callable, Optional
from voice_companion.noise_filter import NoiseFilter

logger = logging.getLogger(__name__)

class InterruptManager:
    """Monitors the microphone while TTS is playing to detect interruptions."""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.noise_filter = NoiseFilter(dynamic_energy_threshold=False)
        self._stop_func: Optional[Callable] = None
        
    def start_monitoring(self, on_interrupt: Callable):
        if self._stop_func:
            return
            
        mic = sr.Microphone()
        with mic as source:
            # Quick calibration
            self.noise_filter.apply(self.recognizer, source, duration=0.5)
            
        # We increase the energy threshold slightly so the speakers don't trigger the mic as easily
        self.recognizer.energy_threshold += 200 
        
        def callback(recognizer, audio):
            # If audio triggered the recognizer, someone is likely talking
            # We don't even need to transcribe it to interrupt, just the sound is enough
            logger.warning("Voice Activity Detected! Interrupting TTS...")
            on_interrupt()
            self.stop_monitoring()
            
        self._stop_func = self.recognizer.listen_in_background(mic, callback, phrase_time_limit=2)
        
    def stop_monitoring(self):
        if self._stop_func:
            self._stop_func(wait_for_stop=False)
            self._stop_func = None
