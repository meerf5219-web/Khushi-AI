import pytest
from unittest.mock import MagicMock
from agents.coordinator import CoordinatorAgent
from agents.specialized.memory import MemoryAgent
from brain.event_bus import event_bus

def test_coordinator_json_parser():
    """Verify that Coordinator correctly parses LLM JSON execution plans."""
    coord = CoordinatorAgent()
    
    valid_output = '''
    ```json
    [
      {"agent": "memory", "payload": {"action": "search", "query": "UPSC"}}
    ]
    ```
    '''
    
    plan = coord._parse_execution_plan(valid_output)
    assert len(plan) == 1
    assert plan[0]["agent"] == "memory"
    assert plan[0]["payload"]["action"] == "search"

def test_coordinator_delegation_flow():
    """Verify Coordinator sends to EventBus and waits for reply."""
    brain = MagicMock()
    # Mock LLM to return a simple plan
    brain.llm.generate.side_effect = [
        '[{"agent": "memory", "payload": {"action": "search", "query": "UPSC"}}]',
        "Final Synthesis"
    ]
    
    # Initialize MemoryAgent to actually receive the event bus call
    mem_agent = MemoryAgent(brain=brain)
    
    coord = CoordinatorAgent(brain=brain)
    
    # Execute
    result = coord.execute_task("Find UPSC syllabus")
    
    assert result["status"] == "success"
    assert "memory" in result["agent_results"]
    assert result["final_answer"] == "Final Synthesis"
    
def test_coordinator_timeout_handling():
    """Verify Coordinator safely aborts if an agent doesn't reply in time."""
    brain = MagicMock()
    brain.llm.generate.return_value = '[{"agent": "black_hole", "payload": {}}]'
    
    coord = CoordinatorAgent(brain=brain)
    
    # We set a tiny timeout for the test to ensure it fails fast
    # Mocking the sync_client request directly to avoid actual sleeping
    original_request = coord.sync_client.request
    
    def fast_fail_request(target, payload, timeout):
        return original_request(target, payload, timeout=0.1)
        
    coord.sync_client.request = fast_fail_request
    
    result = coord.execute_task("Do impossible task")
    
    assert result["agent_results"]["black_hole"] == "Timeout"
