import logging
from typing import Optional, Any
from PySide6.QtCore import QObject, Signal

from brain.event_bus import event_bus
from voice_companion.listener import ContinuousListener
from voice_companion.wakeword import WakeWordDetector
from voice_companion.interrupt_manager import InterruptManager
from voice_companion.stream_tts import StreamingTTS
from voice_companion.workers import VoiceWorker

logger = logging.getLogger(__name__)

class SpeechRouter(QObject):
    """
    Central controller for Generation 4.5: Full-Duplex Voice Companion.
    """
    
    def __init__(self, brain: Any = None):
        super().__init__()
        self.brain = brain
        self.wakeword = WakeWordDetector()
        self.listener = ContinuousListener()
        self.interruptor = InterruptManager()
        self.tts = StreamingTTS()
        
        self.active_worker: Optional[VoiceWorker] = None
        self.is_listening = False
        
    def start_service(self):
        self.tts.start()
        self._start_wakeword()
        logger.info("Voice Companion service started.")
        
    def stop_service(self):
        self.wakeword.stop()
        self.interruptor.stop_monitoring()
        self.tts.stop()
        if self.active_worker:
            self.active_worker.cancel()
        
    def _start_wakeword(self):
        self.is_listening = False
        self.wakeword.start(self._on_wakeword_detected)
        
    def _on_wakeword_detected(self):
        self.wakeword.stop()
        event_bus.publish("voice_companion", {"topic": "WAKEWORD_DETECTED"})
        self._start_listening_session()
        
    def _start_listening_session(self):
        self.is_listening = True
        
        if self.active_worker:
            self.active_worker.cancel()
            
        self.active_worker = VoiceWorker("listen_once", self.listener.listen_once)
        
        def on_completed(name, text):
            if text:
                logger.info(f"User said: {text}")
                self._process_command(text)
            else:
                self._start_wakeword() # Go back to sleep
                
        def on_failed(name, err):
            logger.error(f"Voice worker failed: {err}")
            self._start_wakeword()
            
        self.active_worker.completed_action.connect(on_completed)
        self.active_worker.failed_action.connect(on_failed)
        self.active_worker.interrupted_action.connect(lambda n: self._start_wakeword())
        self.active_worker.start()
        
    def _process_command(self, text: str):
        # We route this through the main brain
        if not self.brain:
            logger.warning("Brain not connected to SpeechRouter.")
            self._start_wakeword()
            return
            
        event_bus.publish("voice_companion", {"topic": "VOICE_STARTED"})
        
        # Parse intent (using correct IntentEngine detect api)
        intent_payload = self.brain.intent.detect(text)
        intent = intent_payload.get("intent", "CHAT")
        entity = intent_payload.get("entity")
        
        # Route voice command through the full conversation pipeline so voice and typed chat work identically
        response = self.brain.think(text)
        
        # Publish interaction event to EventBus for GUI chat history sync
        event_bus.publish("VOICE_COMPANION_INTERACTION", {
            "user_text": text,
            "assistant_response": response
        })
        
        # Start TTS
        self.tts.stop_event.clear()
        
        # Speak asynchronously if not already triggered by OllamaProvider chunks
        import voice.speaker as speaker_module
        if not speaker_module._has_spoken_in_turn:
            speaker_module._has_spoken_in_turn = True
            # Split into sentences for pseudo-streaming
            import re
            sentences = re.split(r'(?<=[.!?]) +', str(response))
            for sentence in sentences:
                self.tts.speak_chunk(sentence)
            
        # While TTS is playing, we start the interrupt manager!
        self.interruptor.start_monitoring(self._on_user_interrupted)
        
        # Once TTS is done, we normally want to listen again, but since TTS plays
        # in background, we need a way to know it finished. 
        # For simplicity, we just go back to wakeword.
        self._start_wakeword()
        
    def _on_user_interrupted(self):
        """User spoke over Khushi."""
        self.tts.interrupt()
        event_bus.publish("voice_companion", {"topic": "USER_INTERRUPTED"})
        
        # Immediately start listening to their new command
        self._start_listening_session()
        
# Singleton reference for router/UI integration
voice_router = SpeechRouter()
