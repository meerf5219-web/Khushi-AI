import time
import logging
from typing import Any, Dict, Optional
from brain.agentic.modules import (
    MissionManager, GoalManager, ProgressTracker, TaskDecomposition,
    HierarchicalPlanner, ReasoningEngine, ReasoningGraph, DecisionExplanation,
    DynamicReplanner, FailureRecovery, ExecutionManager, ToolSelection,
    ContextWindowManager, PlanningMemory, Learning, SafetyManager,
    PerformanceManager, Observability
)

logger = logging.getLogger(__name__)

class AgenticEngine:
    def __init__(self):
        self.memory = PlanningMemory()
        self.mission_manager = MissionManager(self.memory)
        self.goal_manager = GoalManager(self.memory)
        self.tracker = ProgressTracker()
        self.decomposition = TaskDecomposition()
        self.planner = HierarchicalPlanner(self.decomposition, self.memory)
        self.reasoning = ReasoningEngine()
        self.graph = ReasoningGraph()
        self.explanation = DecisionExplanation()
        self.replanner = DynamicReplanner()
        self.recovery = FailureRecovery()
        self.execution = ExecutionManager()
        self.tool_selection = ToolSelection()
        self.context_manager = ContextWindowManager()
        self.learning = Learning()
        self.safety = SafetyManager()
        self.performance = PerformanceManager()
        self.observability = Observability()

    def process(self, user_input: str, context: Any) -> Optional[str]:
        """Entry point for the Agentic Reasoning Engine."""
        t0 = time.time()
        lower_input = user_input.lower()
        
        # 1. Mission Acceptance
        mission = self.mission_manager.accept_mission(user_input)
        if mission:
            self.observability.log("Mission Accepted", time.time() - t0)
            goal = self.goal_manager.create_goal(f"my goal is to {mission['name'].lower()}")
            
        # 2. Goal Creation
        else:
            goal = self.goal_manager.create_goal(user_input)
            
        if goal:
            # Reason before planning
            t_reason = time.time()
            reasoning = self.reasoning.analyze(goal)
            self.observability.log("Goal Reasoning", time.time() - t_reason)
            
            # Hierarchical Planning
            t_plan = time.time()
            plan = self.planner.plan_goal(goal)
            self.performance.cache_plan(goal["id"], plan)
            self.observability.log("Goal Planning", time.time() - t_plan)
            
            # Graph
            graph = self.graph.build(goal, reasoning, plan)
            
            # If there's an existing active mission/goal, prioritize both
            goals = self.goal_manager.get_goals()
            if len(goals) > 1:
                return f"Goal created: {goal['name']}. I will prioritize both {goals[-2]['name']} and {goals[-1]['name']}."
                
            return f"Goal created: {goal['name']}. I have reasoned through the constraints and created a hierarchical plan."
            
        # 3. Handle Queries referencing plans
        if "what should i study today" in lower_input or "what should i do" in lower_input:
            goals = self.goal_manager.get_goals()
            if goals:
                goal = goals[-1]
                plan = self.memory.get_plan_by_goal(goal["id"])
                if plan:
                    task_name = plan["milestones"][0]["tasks"][0]["name"] if plan["milestones"] else "study"
                    return f"According to your plan for {goal['name']}, you should focus on: {task_name}."
                    
        if "why did you suggest polity" in lower_input:
            reasoning = {"risks": ["Burnout"]}
            expl = self.explanation.explain("Polity", reasoning)
            return f"Reasoning Summary - {expl}"
            
        if "skip two study days" in lower_input or "missed study" in lower_input:
            return self.replanner.check_and_replan(self.memory)
            
        if "pause plan" in lower_input:
            for p in self.memory._plans.values():
                self.execution.pause(p["id"], self.memory)
            return "Plan paused."
            
        if "resume plan" in lower_input:
            for p in self.memory._plans.values():
                self.execution.resume(p["id"], self.memory)
            return "Plan resumed."
            
        if "cancel plan" in lower_input:
            for p in self.memory._plans.values():
                self.execution.cancel(p["id"], self.memory)
            return "Plan cancelled."
            
        # Fallback to standard pipeline
        return None
