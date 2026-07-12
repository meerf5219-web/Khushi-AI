import pyttsx3
import logging
from queue import Queue
from threading import Thread, Event
from typing import Optional
from voice_companion.profiles import get_profile

logger = logging.getLogger(__name__)

class StreamingTTS:
    """Handles chunked Text-To-Speech with instant interruption."""
    
    def __init__(self):
        self.engine = None
        self.queue: Queue = Queue()
        self.is_running = False
        self.stop_event = Event()
        self.thread = None
        
    def _init_engine(self, profile_name: str):
        pass
            
    def _worker(self):
        pass

    def start(self, profile_name: str = "default"):
        self.is_running = True
        self.stop_event.clear()
            
    def stop(self):
        self.is_running = False
        self.interrupt()
            
    def speak_chunk(self, text: str):
        """Adds a phrase/sentence to the audio queue and routes to unified speaking engine."""
        if self.stop_event.is_set():
            return
        self.queue.put(text)
        from voice.speaker import speaking_engine
        speaking_engine.speak(text, cancel_previous=False, block=False)
        
    def interrupt(self):
        """Instantly halts TTS and clears the queue."""
        self.stop_event.set()
        
        # Clear queue
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except:
                pass
                
        from voice.speaker import speaking_engine
        speaking_engine.cancel()
            
        logger.info("TTS Interrupted and queue cleared.")
