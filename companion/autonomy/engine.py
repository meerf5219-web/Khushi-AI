import time
import logging
from PySide6.QtCore import QThread, Signal
from companion.autonomy.context import IdleMonitor, ProductivityScorer
from companion.autonomy.config import CURRENT_AUTONOMY_LEVEL, AutonomyLevel
from companion.autonomy.agents.briefing import BriefingAgent
from companion.autonomy.agents.suggestion import SuggestionAgent
from brain.event_bus import event_bus

logger = logging.getLogger(__name__)

class ProactiveEngine(QThread):
    """
    Background thread that monitors the desktop context and triggers autonomous agents.
    """
    suggestion_ready = Signal(dict)
    started = Signal()
    progress = Signal(int, str)
    finished = Signal()
    error = Signal(str)
    
    def __init__(self, brain=None):
        super().__init__()
        self.brain = brain
        self.idle_monitor = IdleMonitor()
        self.productivity_scorer = ProductivityScorer()
        
        self.briefing_agent = BriefingAgent(brain)
        self.suggestion_agent = SuggestionAgent(brain)
        
        self.running = False
        self.last_idle_trigger = 0
        
    def run(self):
        self.started.emit()
        self.running = True
        logger.info("Autonomous Companion Core Started.")
        
        # In a real app we'd track the date for morning briefings.
        # For simplicity, we just loop monitoring idle states.
        
        while self.running:
            try:
                self.progress.emit(10, "Checking idle duration...")
                idle_sec = self.idle_monitor.get_idle_duration()
                
                # If idle for 5 minutes (300 sec) and we haven't triggered recently
                if idle_sec > 300 and (time.time() - self.last_idle_trigger > 3600):
                    logger.info("Idle threshold reached. Generating suggestion...")
                    self.last_idle_trigger = time.time()
                    
                    if CURRENT_AUTONOMY_LEVEL >= AutonomyLevel.LEVEL_1_SUGGEST:
                        self.progress.emit(50, "Generating idle suggestion...")
                        suggestion = self.suggestion_agent.generate_idle_suggestion(int(idle_sec / 60))
                        if suggestion:
                            self.suggestion_ready.emit(suggestion)
                            event_bus.publish("autonomy", {"topic": "SUGGESTION_CREATED", "data": suggestion})
                            self.progress.emit(100, "Suggestion generated successfully.")
                            
            except Exception as e:
                logger.error(f"Error in ProactiveEngine loop: {e}")
                self.error.emit(str(e))
                
            # Sleep 10 seconds between checks to save CPU
            time.sleep(10)
            
        self.finished.emit()

    def stop(self):
        self.running = False
        self.wait()
