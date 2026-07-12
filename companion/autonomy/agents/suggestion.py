import logging
from companion.autonomy.safety import wrap_autonomous_prompt, parse_autonomous_response

logger = logging.getLogger(__name__)

class SuggestionAgent:
    """
    Generates mid-day suggestions based on idle metrics or active window focus.
    """
    def __init__(self, brain=None):
        self.brain = brain
        
    def generate_idle_suggestion(self, idle_minutes: int) -> dict:
        if not self.brain: return None
        
        prompt = (
            f"The user has been idle for {idle_minutes} minutes. "
            "Suggest a productive micro-task or ask if they need help starting work on their goals."
        )
        safe_prompt = wrap_autonomous_prompt(prompt)
        response_text = self.brain.llm.generate(safe_prompt)
        return parse_autonomous_response(response_text)
