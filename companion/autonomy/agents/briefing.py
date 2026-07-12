import time
import logging
from companion.autonomy.safety import wrap_autonomous_prompt, parse_autonomous_response

logger = logging.getLogger(__name__)

class BriefingAgent:
    """
    Creates morning and evening briefs.
    """
    def __init__(self, brain=None):
        self.brain = brain
        
    def generate_morning_brief(self) -> dict:
        """Asks the Brain LLM to create a morning brief."""
        if not self.brain:
            return None
            
        # Collect context
        try:
            profile = self.brain.cie.get_profile()
            goals = self.brain.cie.get_goals()
        except:
            profile = {}
            goals = []
            
        prompt = (
            f"The user has just started their computer for the day. "
            f"Current Goals: {goals}\\n"
            f"Create a highly concise morning briefing suggesting what to tackle first."
        )
        
        safe_prompt = wrap_autonomous_prompt(prompt)
        # Execute blocking LLM call (this must be run in background worker)
        response_text = self.brain.llm.generate(safe_prompt)
        
        return parse_autonomous_response(response_text)

    def generate_evening_reflection(self) -> dict:
        if not self.brain:
            return None
            
        prompt = "The user has been working all day. Provide a short reflection prompt to help them wind down and summarize achievements."
        safe_prompt = wrap_autonomous_prompt(prompt)
        response_text = self.brain.llm.generate(safe_prompt)
        
        return parse_autonomous_response(response_text)
