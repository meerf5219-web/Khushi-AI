import speech_recognition as sr
import logging

logger = logging.getLogger(__name__)

class NoiseFilter:
    """Configures microphone for ambient noise gating."""
    
    def __init__(self, energy_threshold: int = 400, dynamic_energy_threshold: bool = True):
        self.energy_threshold = energy_threshold
        self.dynamic_energy_threshold = dynamic_energy_threshold
        
    def apply(self, recognizer: sr.Recognizer, mic: sr.Microphone, duration: float = 1.0):
        """Calibrates the recognizer to the current ambient noise level."""
        recognizer.energy_threshold = self.energy_threshold
        recognizer.dynamic_energy_threshold = self.dynamic_energy_threshold
        
        logger.info(f"Calibrating noise filter for {duration} seconds...")
        recognizer.adjust_for_ambient_noise(mic, duration=duration)
        logger.info(f"Calibrated. Energy threshold is now {recognizer.energy_threshold}.")
