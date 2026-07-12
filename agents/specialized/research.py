from typing import Any
from agents.base import BaseAgent, AgentContext

class ResearchAgent(BaseAgent):
    """
    Specialized agent for scraping data and searching the web.
    """
    def __init__(self, brain):
        super().__init__("research", brain)

    def process(self, context: AgentContext) -> Any:
        query = context.payload.get("query")
        if not query:
            raise ValueError("ResearchAgent requires a 'query' in payload.")
            
        # In a real system, this would interact with BrowserController
        # For this prototype, we simulate a web search via the LLM.
        if not self.brain:
            return {"error": "Brain missing."}
            
        prompt = f"Perform a highly factual summarized web search simulation for: {query}"
        response = self.brain.llm.generate(prompt)
        
        return {"summary": response}
