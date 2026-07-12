import json
import logging
from typing import Dict, Any

from agents.base import SyncAgentClient

logger = logging.getLogger(__name__)

class CoordinatorAgent:
    """
    The master agent that delegates multi-step workflows to specialized agents.
    """
    def __init__(self, brain=None):
        self.brain = brain
        self.sync_client = SyncAgentClient(reply_channel="agent.coordinator.reply")
        
    def _parse_execution_plan(self, llm_response: str) -> list:
        """
        Extracts JSON from LLM output.
        Format expected:
        [
          {"agent": "memory", "payload": {"action": "search", "query": "XYZ"}},
          {"agent": "research", "payload": {"query": "XYZ"}}
        ]
        """
        try:
            clean = llm_response.strip()
            if "```json" in clean:
                clean = clean.split("```json")[1].split("```")[0].strip()
            return json.loads(clean)
        except Exception as e:
            logger.error(f"Failed to parse execution plan: {e}")
            return []

    def execute_task(self, user_intent: str) -> Dict[str, Any]:
        """
        Coordinates a complex multi-step task.
        """
        logger.info(f"Coordinator analyzing intent: {user_intent}")
        
        # 1. Ask Brain to generate an execution plan
        prompt = (
            f"You are the Coordinator Agent. Break down the user intent into a JSON list of sub-tasks.\\n"
            f"Available agents: 'memory', 'research', 'automation', 'vision'.\\n"
            f"User intent: {user_intent}\\n"
            f"Output strictly a JSON list of objects: [{{\"agent\": \"name\", \"payload\": {{...}}}}]"
        )
        
        plan_response = self.brain.llm.generate(prompt)
        plan = self._parse_execution_plan(plan_response)
        
        if not plan:
            return {"status": "error", "message": "Coordinator failed to formulate an execution plan."}
            
        logger.info(f"Coordinator generated execution plan: {plan}")
        
        # 2. Delegate to agents sequentially (could be parallelized with threads)
        results = {}
        for step in plan:
            target_agent = step.get("agent")
            payload = step.get("payload", {})
            
            if not target_agent: continue
            
            logger.info(f"Coordinator delegating step to {target_agent}...")
            # Use synchronous event bus wrapper with 30s timeout
            reply = self.sync_client.request(target_agent, payload, timeout=30)
            
            results[target_agent] = reply.get("result", reply.get("error"))
            
            # Fast fail
            if reply.get("status") == "error":
                logger.error(f"Sub-agent {target_agent} failed. Aborting plan.")
                break
                
        # 3. Synthesize final answer
        synth_prompt = (
            f"The user asked: {user_intent}\\n"
            f"The specialized agents returned the following data: {json.dumps(results, default=str)}\\n"
            f"Synthesize a cohesive and helpful final answer for the user."
        )
        final_answer = self.brain.llm.generate(synth_prompt)
        
        return {
            "status": "success",
            "execution_plan": plan,
            "agent_results": results,
            "final_answer": final_answer
        }
