import time
import pytest
from brain.agentic.engine import AgenticEngine
from brain.agentic.modules import PlanningMemory

def test_generation3_manual_verification():
    engine = AgenticEngine()
    
    # 1. Create Goal
    resp1 = engine.process("My goal is to crack UPSC", context={})
    assert resp1 is not None
    assert "goal created" in resp1.lower()
    assert "upsc" in resp1.lower()
    
    # Verify persistence in planning memory
    goals = engine.goal_manager.get_goals()
    assert len(goals) == 1
    assert goals[0]["name"] == "upsc preparation"
    
    # Verify hierarchical plan exists
    plan = engine.memory.get_plan_by_goal(goals[0]["id"])
    assert plan is not None
    assert plan["milestones"][0]["tasks"][0]["name"] == "Finish NCERT"
    
    # 2. Ask what to study
    resp2 = engine.process("What should I study today?", context={})
    assert resp2 is not None
    assert "According to your plan for upsc preparation, you should focus on: Finish NCERT" in resp2
    
    # 3. Skip two study days -> Replan
    resp3 = engine.process("I skip two study days", context={})
    assert resp3 is not None
    assert "dynamically replanning" in resp3.lower()
    
    # 4. Create second goal -> Prioritize both
    resp4 = engine.process("My goal is to Build Khushi AI", context={})
    assert resp4 is not None
    assert "prioritize both" in resp4.lower()
    assert "build khushi ai" in resp4.lower()
    
    # 5. Why did you suggest Polity
    resp5 = engine.process("Why did you suggest Polity?", context={})
    assert resp5 is not None
    assert "WHY:" in resp5
    assert "Burnout" in resp5
    
    # 6. Pause, Resume, Cancel transitions
    engine.process("pause plan", context={})
    plan2 = engine.memory.get_plan_by_goal(goals[0]["id"])
    assert plan2["status"] == "paused"
    
    engine.process("resume plan", context={})
    plan3 = engine.memory.get_plan_by_goal(goals[0]["id"])
    assert plan3["status"] == "active"
    
    engine.process("cancel plan", context={})
    plan4 = engine.memory.get_plan_by_goal(goals[0]["id"])
    assert plan4["status"] == "cancelled"

def test_mission_persists():
    engine = AgenticEngine()
    resp = engine.process("Help me prepare UPSC", context={})
    assert resp is not None
    assert "Goal created" in resp
    
    missions = engine.mission_manager.get_active_missions()
    assert len(missions) == 1
    assert missions[0]["name"] == "UPSC Preparation"
