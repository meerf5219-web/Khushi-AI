from typing import Any
from agents.base import BaseAgent, AgentContext

class MemoryAgent(BaseAgent):
    """
    Specialized agent for searching and saving long-term memories.
    """
    def __init__(self, brain):
        super().__init__("memory", brain)

    def process(self, context: AgentContext) -> Any:
        action = context.payload.get("action")
        
        if action == "search":
            query = context.payload.get("query", "")
            # Simplistic lookup. A real implementation uses CIE memory embeddings.
            if not self.brain or not hasattr(self.brain, "memory"):
                return {"error": "Brain memory missing."}
                
            # If CIE is available, query it
            if hasattr(self.brain, "cie"):
                results = self.brain.cie.search(query)
                return {"results": results}
                
            return {"results": f"Simulated memory search for: {query}"}
            
        elif action == "save":
            fact = context.payload.get("fact", "")
            if hasattr(self.brain, "cie"):
                self.brain.cie.extract_and_store(fact)
                return {"status": "saved", "fact": fact}
                
            return {"status": "simulated_save", "fact": fact}
            
        else:
            raise ValueError(f"Unknown MemoryAgent action: {action}")
