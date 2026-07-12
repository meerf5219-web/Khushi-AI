from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ConversationPipeline:
    """
    Main Conversation Pipeline (Phase 7.5)
    ======================================
    Implements: Input → Context → Emotion → Memory → Reasoning → Knowledge → Planner → Response Composer → Voice
    Tracks active context stack, topic flow, session summaries, and recoveries.
    """

    context_stack: List[str] = field(default_factory=list)
    active_topic: Optional[str] = None
    response_composer: Any = field(init=False, default=None)

    def __post_init__(self) -> None:
        from brain.response_composer.engine import ResponseComposer
        self.response_composer = ResponseComposer()
        
        from brain.prediction.engine import PredictionEngine
        self.prediction_engine = None

        from brain.event_store.sqlite_store import SQLiteEventStore
        self.event_store = SQLiteEventStore()
        self.event_processor = None

    def execute(self, text: str, brain: Any) -> str:
        """
        Execute the multi-stage conversational pipeline.
        """
        t0 = time.perf_counter()
        logger.info("ConversationPipeline: Starting execution for '%s'", text)

        # -------------------------------------------------------------
        # STAGE 1: Context (Topic tracking, stack, pronoun resolution)
        # -------------------------------------------------------------
        # 1.1 Pronoun resolution
        rewritten_text = brain.context.rewrite(text)

        # 1.2 Conversation recovery check
        if any(keyword in rewritten_text.lower() for keyword in ["recover topic", "go back to previous topic", "where were we"]):
            recovered = self.recover_context()
            logger.info("ConversationPipeline: Recovered context topic='%s'", recovered)
            rewritten_text = f"show my {recovered}" if recovered else rewritten_text

        # 1.3 Update context stack & topic tracking
        self._update_context_stack(rewritten_text)

        # -------------------------------------------------------------
        # STAGE 1.5: Raw Event Logging
        # -------------------------------------------------------------
        if self.event_processor is None:
            from brain.event_store.processor import EventProcessor
            self.event_processor = EventProcessor(self.event_store, brain.memory)

        event_data = {
            "timestamp": time.time(),
            "session_id": getattr(brain, "session_id", ""),
            "conversation_id": "",
            "source": "user",
            "speaker": brain.user_name or "user",
            "raw_text": text,
            "normalized_text": rewritten_text,
            "metadata": {"topic": self.active_topic},
            "schema_version": 1
        }
        self.event_store.append_event(event_data)
        
        # Synchronously process the raw event to derive memories (Semantic, Predictions, etc)
        self.event_processor.process_pending()

        # -------------------------------------------------------------
        # STAGE 2: Emotion (Stress, burnout, celebrating, confidence)
        # -------------------------------------------------------------
        brain.current_emo_state = brain.emotional_engine.analyze_text(rewritten_text)

        # -------------------------------------------------------------
        # STAGE 3: Memory (Personalizations & preferences learning)
        # -------------------------------------------------------------
        profile_data = brain.cie.get_profile()
        # Analyze and update interaction preferences
        style_instructions = ""
        if hasattr(brain, "preference_engine"):
            brain.preference_engine.analyze_and_update(rewritten_text, brain.cie._store)
            style_instructions = brain.preference_engine.get_style_instructions(brain.cie._store)

        # Try early personalized response lookup
        personalized_resp = brain.emotional_engine.personalize_response(
            brain.current_emo_state, rewritten_text, profile_data
        )
        if personalized_resp:
            logger.info("ConversationPipeline: Bypassing to personalized memory response.")
            # Format through Response Composer (Stage 7) & Voice (Stage 8)
            composed = self.response_composer.compose(
                personalized_resp,
                brain.current_emo_state,
                style_instructions,
                profile_data
            )
            voice_ready = self._format_voice(composed)
            brain.context.update(text, voice_ready)
            brain._record_turn(text, voice_ready)
            return voice_ready

        # -------------------------------------------------------------
        # STAGE 3.5: Prediction Engine (Generation 2)
        # -------------------------------------------------------------
        if self.prediction_engine is None:
            from brain.prediction.engine import PredictionEngine
            self.prediction_engine = PredictionEngine(brain.memory)

        prediction_suggestion = self.prediction_engine.observe_and_predict(
            user_input=rewritten_text,
            active_topic=self.active_topic,
            recent_turns=brain.recent_turns,
            emo_state=getattr(brain, "current_emo_state", {})
        )

        # -------------------------------------------------------------
        # STAGE 3.7: Agentic Reasoning (Generation 3)
        # -------------------------------------------------------------
        if not hasattr(self, "agentic_engine"):
            from brain.agentic.engine import AgenticEngine
            self.agentic_engine = AgenticEngine()
            
        agentic_response = self.agentic_engine.process(rewritten_text, brain.context)
        if agentic_response:
            logger.info("ConversationPipeline: Bypassing to Agentic Reasoning.")
            
            # STAGE 3.8: Internal Thought Engine
            if not hasattr(self, "thought_engine"):
                from brain.agentic.thought import InternalThoughtEngine
                self.thought_engine = InternalThoughtEngine()
                
            refined_response, thought_metrics = self.thought_engine.process_thought(
                rewritten_text, brain.context, agentic_response
            )
            
            # Format through Response Composer (Stage 7) & Voice (Stage 8)
            composed = self.response_composer.compose(
                refined_response,
                brain.current_emo_state,
                style_instructions,
                profile_data
            )
            voice_ready = self._format_voice(composed)
            
            # STAGE 8.5: Self Evaluation Engine
            if not hasattr(self, "evaluation_engine"):
                from brain.agentic.evaluation import SelfEvaluationEngine
                self.evaluation_engine = SelfEvaluationEngine()
                
            self.evaluation_engine.evaluate_turn(rewritten_text, voice_ready, brain.context)
            
            brain.context.update(text, voice_ready)
            brain._record_turn(text, voice_ready)
            return voice_ready

        # -------------------------------------------------------------
        # STAGE 4: Reasoning (Pipeline processing, intent, ambiguity)
        # -------------------------------------------------------------
        result = brain.pipeline.process(rewritten_text, brain.recent_turns)

        # -------------------------------------------------------------
        # STAGE 5: Knowledge (RAG / Web Search lookups)
        # -------------------------------------------------------------
        # ContextRouter and response optimizer decides if local RAG/skills/knowledge is needed.
        # This is handled during single query execution in brain.

        # -------------------------------------------------------------
        # STAGE 6: Planner & Routing
        # -------------------------------------------------------------
        # 1. Multi-Intent split parsing
        if result.is_multi_intent and len(result.sub_queries) > 1:
            responses = []
            for sub_q in result.sub_queries:
                resp = brain._process_single_query(sub_q, t0)
                responses.append(resp)
            raw_response = " and ".join(responses)
        # 2. Ambiguity clarification
        elif result.ambiguity.is_ambiguous:
            raw_response = result.ambiguity.clarification_question
        # 3. Contextual Routing response
        elif result.contextual_response is not None:
            raw_response = result.contextual_response
        # 4. Learning corrections response
        elif brain.pipeline.learning_engine.is_correction(result.corrected_query):
            # Extract target and message
            target = brain.pipeline.learning_engine.extract_correction_target(result.corrected_query)
            last_query = ""
            for turn in reversed(brain.recent_turns):
                lq = turn.get("user_input", "")
                if lq and not brain.pipeline.learning_engine.is_correction(lq):
                    last_query = lq
                    break
            if last_query:
                success, msg = brain.pipeline.learning_engine.learn(last_query, result.corrected_query)
                raw_response = msg
            else:
                raw_response = "I am programmed to assist with your objectives based on stored guidelines."
        else:
            raw_response = brain._process_single_query_with_result(result, rewritten_text, t0)

        # -------------------------------------------------------------
        # STAGE 7: Response Composer (Personality constraints & tone)
        # -------------------------------------------------------------
        # Issue 4: Prediction Policy — never inject suggestions into
        # terminal, error, identity, memory, or skill confirmation responses.
        _PREDICTION_BLOCKED = (
            "goodbye", "farewell", "bye",          # shutdown / terminal
            "nice to meet", "your name is",         # identity responses
            "i don't know that yet",                # error fallback
            "i'll remember", "remembered",          # memory confirmations
            "opening ", "launching ", "starting ",  # app / desktop confirmations
            "screenshot", "battery level", "cpu",   # system skill responses
            "sorry faisal",                         # error responses
        )
        if prediction_suggestion:
            raw_lower = raw_response.lower()
            if not any(blocked in raw_lower for blocked in _PREDICTION_BLOCKED):
                raw_response = f"{raw_response} {prediction_suggestion}"

        composed_response = self.response_composer.compose(
            raw_response,
            brain.current_emo_state,
            style_instructions,
            profile_data
        )

        # -------------------------------------------------------------
        # STAGE 8: Voice (Punctuation and formatting cleanup)
        # -------------------------------------------------------------
        voice_response = self._format_voice(composed_response)

        # Finalize turn updates
        brain.context.update(text, voice_response)
        brain._record_turn(text, voice_response)

        elapsed = time.perf_counter() - t0
        logger.info("ConversationPipeline: Completed execution in %.3fs", elapsed)
        return voice_response

    def _update_context_stack(self, text: str) -> None:
        """
        Pushes and pops topics from the context stack depending on input markers.
        """
        low = text.lower().strip()

        # Pop triggers
        if any(keyword in low for keyword in ["nevermind", "go back", "cancel topic", "stop that"]):
            if self.context_stack:
                popped = self.context_stack.pop()
                logger.info("ConversationPipeline: Popped topic='%s' from stack.", popped)
            self.active_topic = self.context_stack[-1] if self.context_stack else None
            return

        # Push triggers
        new_topic = None
        if "weather" in low:
            new_topic = "weather"
        elif "upsc" in low or "goal" in low:
            new_topic = "goals"
        elif "project" in low or "khushi" in low:
            new_topic = "projects"
        elif "chrome" in low or "notepad" in low or "calculator" in low:
            new_topic = "app_launch"

        if new_topic:
            # Avoid duplicate consecutive push
            if not self.context_stack or self.context_stack[-1] != new_topic:
                self.context_stack.append(new_topic)
                logger.info("ConversationPipeline: Pushed topic='%s' to stack.", new_topic)
            self.active_topic = new_topic

    def get_summary(self, turns: List[Dict[str, Any]]) -> str:
        """
        Generates a summary paragraph of the recent conversation history.
        """
        if not turns:
            return "No conversation history."

        topics = []
        for turn in turns:
            inp = turn.get("user_input", "").lower()
            if "weather" in inp:
                topics.append("weather")
            elif "upsc" in inp:
                topics.append("UPSC goals")
            elif "project" in inp:
                topics.append("projects")

        unique_topics = list(dict.fromkeys(topics))
        if unique_topics:
            return f"Conversation covered: {', '.join(unique_topics)}."
        return f"Conversation consisted of {len(turns)} turns."

    def recover_context(self) -> Optional[str]:
        """
        Recovers active context from stack history.
        """
        if self.context_stack:
            return self.context_stack[-1]
        return None

    def _format_voice(self, text: str) -> str:
        """
        Cleans up markdown notation (e.g. *, #, -, •) for screen reader or voice output.
        """
        if not text:
            return ""
        # Strip code block enclosures
        cleaned = re.sub(r"```[a-zA-Z]*\n?", "", text)
        cleaned = cleaned.replace("```", "")
        # Strip markdown symbols
        cleaned = re.sub(r"[\#\*\`•\-]", "", cleaned)
        # Standardize whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned
