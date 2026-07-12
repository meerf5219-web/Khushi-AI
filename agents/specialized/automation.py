from typing import Any
from agents.base import BaseAgent, AgentContext

class AutomationAgent(BaseAgent):
    """
    Specialized agent for automating desktop actions.
    """
    def __init__(self, brain):
        super().__init__("automation", brain)

    def process(self, context: AgentContext) -> Any:
        action = context.payload.get("action")
        target = context.payload.get("target")
        
        if not action:
            raise ValueError("AutomationAgent requires 'action'.")
            
        # In a real system, this forwards to `automation.controller.AutomationController`
        return {"status": "success", "executed": f"{action} on {target}"}

class VisionAgent(BaseAgent):
    """
    Specialized agent for computer vision and screen intelligence.
    """
    def __init__(self, brain):
        super().__init__("vision", brain)

    def process(self, context: AgentContext) -> Any:
        query = context.payload.get("query")
        
        # Forward to `vision.controller.VisionController`
        return {"status": "success", "analysis": f"Simulated vision output for: {query}"}
