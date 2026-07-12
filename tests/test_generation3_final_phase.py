import pytest
from brain.agentic.thought import InternalThoughtEngine
from brain.agentic.evaluation import SelfEvaluationEngine
from brain.agentic.workflow import WorkflowExecutor
from brain.agentic.world import WorldModel

def test_internal_thought_engine():
    engine = InternalThoughtEngine()
    refined, metrics = engine.process_thought("user input", {}, "I don't know the answer.")
    assert metrics["missing_information"] is True
    assert metrics["critique"] == "Need to search for more context."
    assert refined == "I don't know the answer."
    
    refined2, metrics2 = engine.process_thought("user input", {}, "The capital of France is Paris.")
    assert metrics2["missing_information"] is False
    assert metrics2["critique"] == "None"

def test_self_evaluation_engine():
    engine = SelfEvaluationEngine()
    metrics = engine.evaluate_turn("What is UPSC?", "Exam.", {})
    assert "overall_score" in metrics
    assert len(engine.metrics_store) == 1
    
    # Short response penalization
    assert metrics["overall_score"] < 0.9

def test_workflow_executor():
    executor = WorkflowExecutor()
    
    def tool_success(state):
        return "success_data"
        
    def tool_fail(state):
        raise ValueError("Simulated failure")
        
    result = executor.execute_chain([tool_success], {})
    assert result["status"] == "success"
    assert "success_data" in result["results"]
    
    result_fail = executor.execute_chain([tool_fail], {})
    assert result_fail["status"] == "failed"
    assert result_fail["failed_at"] == "tool_fail"
    
def test_world_model():
    world = WorldModel()
    
    world.add_node("u1", "User", {"name": "Alice"})
    world.add_node("p1", "Project", {"name": "UPSC Prep"})
    world.add_edge("u1", "p1")
    
    relationships = world.query_relationships("upsc")
    assert len(relationships) == 1
    assert relationships[0]["label"] == "User"
    assert relationships[0]["metadata"]["name"] == "Alice"
