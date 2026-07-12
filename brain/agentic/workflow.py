import logging
from typing import List, Dict, Any, Callable

logger = logging.getLogger(__name__)

class WorkflowExecutor:
    """Chains multiple tools dynamically."""
    
    def __init__(self):
        self.history = []
        
    def execute_chain(self, tools: List[Callable], context: Any) -> Dict[str, Any]:
        """
        Executes a sequence of tools.
        Supports retry, rollback, and failure recovery.
        """
        state = {"context": context, "results": []}
        
        for tool in tools:
            success = False
            retries = 3
            
            while not success and retries > 0:
                try:
                    result = tool(state)
                    state["results"].append(result)
                    success = True
                except Exception as e:
                    retries -= 1
                    logger.warning(f"Tool {tool.__name__} failed. Retries left: {retries}. Error: {e}")
                    
            if not success:
                logger.error(f"Chain failed at {tool.__name__}. Initiating rollback.")
                self._rollback(state)
                return {"status": "failed", "failed_at": tool.__name__}
                
        return {"status": "success", "results": state["results"]}
        
    def _rollback(self, state: Dict[str, Any]) -> None:
        """Rolls back the state."""
        state["results"] = []
        logger.info("Rollback complete.")
