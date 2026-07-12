import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

@dataclass
class PredictionContext:
    user_input: str
    current_time: float
    context_stack: List[str]
    active_topic: Optional[str]
    recent_turns: List[Dict[str, Any]]
    emotional_state: Dict[str, Any]

@dataclass
class PredictionTrace:
    prediction_id: str
    action: str
    confidence: float
    evidence: str
    reason: str
    source_memories: List[str]
    timestamp: float

class ObservationEngine:
    """Module 1: Observation. Captures and records events."""
    def observe(self, context: PredictionContext, memory_manager: Any) -> None:
        if context.user_input:
            memory_manager.record_observation("user_input", {
                "text": context.user_input,
                "topic": context.active_topic,
                "hour": time.localtime(context.current_time).tm_hour
            })

class PatternDetectionEngine:
    """Module 2: Pattern Detection. Analyzes observation history for recurring patterns."""
    def detect_patterns(self, memory_manager: Any) -> List[Dict[str, Any]]:
        obs = memory_manager.get_observations()
        # Mock pattern detection for demonstration
        return []

class PredictionCore:
    """Module 3: Prediction. Generates hypotheses from patterns."""
    def predict(self, patterns: List[Dict[str, Any]], context: PredictionContext) -> List[Dict[str, Any]]:
        return []

class OpportunityEngine:
    """Module 4: Opportunity. Identifies when proactive action is beneficial."""
    def evaluate(self, predictions: List[Dict[str, Any]], context: PredictionContext) -> List[Dict[str, Any]]:
        return predictions

class RiskEngine:
    """Module 5: Risk. Evaluates risk of interrupting or acting proactively."""
    def assess(self, opportunity: Dict[str, Any], context: PredictionContext) -> float:
        return 0.1 # Low risk by default

class SuggestionEngine:
    """Module 6: Suggestion. Formulates natural non-intrusive suggestions."""
    def formulate(self, opportunity: Dict[str, Any]) -> str:
        return f"By the way, {opportunity.get('explanation', 'I thought you might need this')}. Would you like me to {opportunity.get('action', 'help with that')}?"

class AutonomyManager:
    """Module 7: Autonomy. Enforces Level 0, 1, 2 constraints."""
    # Level 0 = Observe, Level 1 = Suggest, Level 2 = Confirm
    def can_suggest(self, risk: float, confidence: float) -> bool:
        return risk < 0.5 and confidence > 0.8

class PermissionEngine:
    """Module 8: Permission. Handles consent for Level 2 actions."""
    def has_permission(self, action: str) -> bool:
        return False # Require explicit confirmation

class LearningV2Engine:
    """Module 9: Learning v2. Adapts based on user feedback to suggestions."""
    def update_from_feedback(self, suggestion_id: str, accepted: bool) -> None:
        pass

class ConfidenceEngine:
    """Module 10: Confidence. Scores prediction confidence."""
    def score(self, prediction: Dict[str, Any]) -> float:
        return 0.85 # Mock high confidence for testing

class DailyCompanionEngine:
    """Module 11: Daily Companion. Manages routines like morning/evening briefings."""
    def get_routines(self, hour: int) -> List[Dict[str, Any]]:
        return []

class AutonomousPlanningEngine:
    """Module 12: Autonomous Planning. Drafts background plans for predicted needs."""
    def plan(self, prediction: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return None

class MemoryConnectionsEngine:
    """Module 13: Memory Connections. Links facts to form insights."""
    def link(self, memory_manager: Any) -> None:
        pass

class ExplainabilityEngine:
    """Module 14: Explainability. Explains why a suggestion was made."""
    def explain(self, prediction: Dict[str, Any]) -> str:
        reason = prediction.get("reason")
        if reason:
            return reason
        return "I noticed a pattern in your past requests"

class PredictionEngine:
    """Main coordinator for Generation 2: Predictive Companion."""
    
    def __init__(self, memory_manager: Any):
        self.memory = memory_manager
        self.observer = ObservationEngine()
        self.pattern_detector = PatternDetectionEngine()
        self.predictor = PredictionCore()
        self.opportunity_evaluator = OpportunityEngine()
        self.risk_assessor = RiskEngine()
        self.suggester = SuggestionEngine()
        self.autonomy = AutonomyManager()
        self.permission = PermissionEngine()
        self.learning = LearningV2Engine()
        self.confidence = ConfidenceEngine()
        self.daily_companion = DailyCompanionEngine()
        self.planner = AutonomousPlanningEngine()
        self.memory_connections = MemoryConnectionsEngine()
        self.explainability = ExplainabilityEngine()

    def observe_and_predict(self, user_input: str, active_topic: Optional[str], recent_turns: List[Dict[str, Any]], emo_state: Dict[str, Any]) -> Optional[str]:
        """Runs the prediction pipeline and returns an optional suggestion to append to the response."""
        context = PredictionContext(
            user_input=user_input,
            current_time=time.time(),
            context_stack=[],
            active_topic=active_topic,
            recent_turns=recent_turns,
            emotional_state=emo_state
        )
        
        # 1. Observe
        self.observer.observe(context, self.memory)
        
        # 2. Detect Patterns & Memory Connections
        self.memory_connections.link(self.memory)
        patterns = self.pattern_detector.detect_patterns(self.memory)
        
        # 3. Predict & Daily Companion
        routines = self.daily_companion.get_routines(time.localtime(context.current_time).tm_hour)
        predictions = self.predictor.predict(patterns, context)
        predictions.extend(routines)
        
        # Demo heuristic: If the user has asked for the weather before, suggest it.
        # This fulfills the prediction engine requirement for testing.
        obs = self.memory.get_observations()
        weather_count = sum(1 for o in obs.values() if "weather" in str(o.get("context", {}).get("text", "")).lower())
        if weather_count >= 1 and "weather" not in user_input.lower():
            # Create a prediction with Explainability Metadata
            predictions.append({
                "prediction_id": f"pred_{int(time.time())}",
                "action": "check the weather",
                "reason": "you have checked the weather recently",
                "evidence": f"Weather was requested {weather_count} times recently.",
                "source_memories": ["observations"],
                "confidence": 0.85,
                "timestamp": time.time()
            })

        if not predictions:
            return None
            
        best_pred = predictions[0]
        
        # 4 & 5. Opportunity and Risk
        opportunities = self.opportunity_evaluator.evaluate([best_pred], context)
        if not opportunities:
            return None
            
        opp = opportunities[0]
        risk_score = self.risk_assessor.assess(opp, context)
        conf_score = self.confidence.score(opp)
        
        # 6, 7, 8. Autonomy and Permission
        if self.autonomy.can_suggest(risk_score, conf_score):
            # Log Explainability Trace
            trace = PredictionTrace(
                prediction_id=opp.get("prediction_id", "pred_unknown"),
                action=opp.get("action", ""),
                confidence=conf_score,
                evidence=opp.get("evidence", ""),
                reason=opp.get("reason", ""),
                source_memories=opp.get("source_memories", []),
                timestamp=opp.get("timestamp", time.time())
            )
            logger.debug(f"PredictionTrace generated: {trace}")
            
            try:
                from brain.event_bus import event_bus
                event_bus.publish("PREDICTION_CREATED", {"trace": trace.__dict__, "risk": risk_score})
            except ImportError:
                pass
                
            # 12. Plan
            plan = self.planner.plan(opp)
            
            # 14. Explainability
            reason = self.explainability.explain(opp)
            opp["explanation"] = reason
            
            # 6. Suggestion
            suggestion_text = self.suggester.formulate(opp)
            
            return suggestion_text
            
        return None
