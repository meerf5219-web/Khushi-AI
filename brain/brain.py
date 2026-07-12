import logging
import time
from typing import Any, Dict, List, Optional

from brain.context import ContextManager
from brain.decision_engine import DecisionEngine
from brain.intent import IntentEngine
from brain.intelligence.pipeline import IntelligencePipeline, PipelineResult
from brain.emotional_intelligence.engine import EmotionalIntelligenceEngine
from brain.interaction_preferences.engine import InteractionPreferenceEngine
from config.personality import NAME, OWNER
from memory.manager import MemoryManager
from planner.planner import Planner
from skills.skill_manager import SkillManager

logger = logging.getLogger(__name__)


class Brain:
    """Coordinate intent detection, routing, memory, and conversation flow."""

    def __init__(self) -> None:
        self.user_name: Optional[str] = None
        
        def _init_step(name: str, func):
            t0 = time.time()
            logger.info(f"[BRAIN INIT] Starting {name}...")
            try:
                res = func()
            except Exception as e:
                logger.error(f"[BRAIN INIT] Failed {name}: {e}", exc_info=True)
                res = None
            elapsed = time.time() - t0
            if elapsed > 3.0:
                logger.warning(f"[BRAIN INIT] SLOW: {name} took {elapsed:.3f}s")
            else:
                logger.info(f"[BRAIN INIT] {name} took {elapsed:.3f}s")
            return res

        self.context = _init_step("ContextManager", lambda: ContextManager())
        self.emotional_engine = _init_step("EmotionalIntelligenceEngine", lambda: EmotionalIntelligenceEngine())
        self.preference_engine = _init_step("InteractionPreferenceEngine", lambda: InteractionPreferenceEngine())

        from companion.engine import CompanionIntelligenceEngine
        self.cie = _init_step("CompanionIntelligenceEngine", lambda: CompanionIntelligenceEngine())
        self.personality = self.cie._personality if self.cie else None

        self.pipeline = _init_step("IntelligencePipeline", lambda: IntelligencePipeline(cie=self.cie, context_manager=self.context))

        from brain.conversation_pipeline import ConversationPipeline
        self.conversation_pipeline = _init_step("ConversationPipeline", lambda: ConversationPipeline())

        self.memory = _init_step("MemoryManager", lambda: MemoryManager(brain=self))
        from brain.agentic.world import WorldModel
        self.world = _init_step("WorldModel", lambda: WorldModel())
        self.planner = _init_step("Planner", lambda: Planner())
        self.skills = _init_step("SkillManager", lambda: SkillManager())
        self.decision_engine = _init_step("DecisionEngine", lambda: DecisionEngine())
        self.intent = _init_step("IntentEngine", lambda: IntentEngine())

        from voice.speaker import speaking_engine
        self.speaking_engine = speaking_engine

        from router import Router
        self.router = _init_step("Router", lambda: Router(self))

        from plugins.manager import PluginManager
        self.plugin_manager = _init_step("PluginManager", lambda: PluginManager(self))
        if self.plugin_manager:
            self.plugin_manager.load_all()
        
        self.recent_turns: List[Dict[str, Any]] = []

    def think(self, text: str) -> str:
        """Process a user utterance and return filtered assistant response."""
        import voice.speaker as speaker_module
        speaker_module._has_spoken_in_turn = False
        return self.conversation_pipeline.execute(text, self)

    def _think_raw(self, text: str) -> str:
        """Raw think logic."""
        normalized_text = text.lower().strip()
        if not normalized_text:
            return ""

        # Analyze user emotions
        emo_state = self.emotional_engine.analyze_text(text)
        profile_data = self.cie.get_profile()
        personalized_resp = self.emotional_engine.personalize_response(emo_state, text, profile_data)
        if personalized_resp:
            self.context.update(text, personalized_resp)
            self._record_turn(text, personalized_resp)
            return personalized_resp

        brain_t0 = time.perf_counter()
        
        # Rewrite references (Pronouns) using context
        context_t0 = time.perf_counter()
        rewritten_text = self.context.rewrite(text)
        context_elapsed = time.perf_counter() - context_t0
        print(f"Context: {context_elapsed:.3f}s")
        logger.info("Rewritten text: %s", rewritten_text)

        # Process query through the Intelligence Layer pipeline
        pipeline_t0 = time.perf_counter()
        result = self.pipeline.process(rewritten_text, self.recent_turns)
        pipeline_elapsed = time.perf_counter() - pipeline_t0
        print(f"Intelligence Layer: {pipeline_elapsed:.3f}s")

        # 1. Multi-Intent Split Parsing
        if result.is_multi_intent and len(result.sub_queries) > 1:
            responses = []
            for sub_q in result.sub_queries:
                resp = self._process_single_query(sub_q, brain_t0)
                responses.append(resp)
            # Join multiple tasks response
            final_resp = " and ".join(responses)
            self.context.update(text, final_resp)
            self._record_turn(text, final_resp)
            return final_resp

        # 2. Ambiguity clarification
        if result.ambiguity.is_ambiguous:
            resp = result.ambiguity.clarification_question
            self.context.update(text, resp)
            self._record_turn(text, resp)
            return resp

        # 3. Contextual Routing response (if resolved directly by ContextRouter)
        if result.contextual_response is not None:
            resp = result.contextual_response
            self.context.update(text, resp)
            self._record_turn(text, resp)
            return resp

        # 4. Learning corrections response (if feedback statement detected and mapping saved)
        if self.pipeline.learning_engine.is_correction(result.corrected_query):
            # Extract target and message
            target = self.pipeline.learning_engine.extract_correction_target(result.corrected_query)
            # Find the last valid query to link
            last_query = ""
            for turn in reversed(self.recent_turns):
                lq = turn.get("user_input", "")
                if lq and not self.pipeline.learning_engine.is_correction(lq):
                    last_query = lq
                    break
            if last_query:
                success, msg = self.pipeline.learning_engine.learn(last_query, result.corrected_query)
                self.context.update(text, msg)
                self._record_turn(text, msg)
                return msg

        # 5. Single intent processing
        final_resp = self._process_single_query_with_result(result, rewritten_text, brain_t0)
        self.context.update(text, final_resp)
        self._record_turn(text, final_resp)
        return final_resp

    def _process_single_query(self, query: str, brain_t0: float) -> str:
        # Process sub-query through pipeline (with multi-intent check disabled/ignored to avoid loops)
        result = self.pipeline.process(query, self.recent_turns)
        return self._process_single_query_with_result(result, query, brain_t0)

    def _process_single_query_with_result(self, result: PipelineResult, rewritten_text: str, brain_t0: float) -> str:
        # Determine intent name
        intent_name = result.routing_intent
        normalized_text = result.rewritten_query.lower().strip()

        # Check local/quick shortcuts first to match exact legacy logic and tests
        if "what is my name" in normalized_text:
            saved_name = self._load_saved_name()
            if saved_name:
                return f"Your name is {saved_name}."
            return "I don't know your name yet."

        if any(
            phrase in normalized_text
            for phrase in [
                "what is my favourite",
                "what is my favorite",
                "what is my favourite ",
                "what is my favorite ",
            ]
        ) and any(ch in normalized_text for ch in [" ", ""]):
            # Use RECALL_MEMORY route directly or memory recall
            key = normalized_text.replace("what is my favourite", "", 1).replace("what is my favorite", "", 1).strip()
            value = self.memory.recall(key)
            if value:
                return f"{key} is {value}."
            # Fall back to RECALL_MEMORY in router
            resp = self.router.route("RECALL_MEMORY", None, text=rewritten_text)
            if resp:
                return resp
            return "I don't have that saved yet."

        if normalized_text.startswith("my name is"):
            name = normalized_text.replace("my name is", "", 1).strip().title()
            self.user_name = name
            self._save_user_name(name)
            return f"Nice to meet you {name}."

        # Detect via IntentEngine if not overridden by high confidence pipeline result
        parsed_intent = self.intent.detect(result.rewritten_query)
        if result.confidence.score < 0.95 or intent_name == "CHAT":
            intent_name = parsed_intent.get("intent", "CHAT")

        # Bypass LLM / direct routing if optimizer decides so or if intent != CHAT
        bypass_llm = result.optimization.get("bypass_llm", False)

        if intent_name != "CHAT":
            # Decide: SKILL or AI
            plan = self.planner.create_plan(result.rewritten_query)
            decision = self.decision_engine.decide(intent_name, plan)
            
            # If bypass_llm is forced, make decision SKILL
            if bypass_llm:
                decision = "SKILL"

            if decision == "AI" and not bypass_llm:
                # LLM execution path
                http_start = time.perf_counter() - brain_t0
                print(f"HTTP_START: {http_start:.3f}s")
                ollama_t0 = time.perf_counter()
                response = self.decision_engine.generate_ai(
                    result.rewritten_query,
                    context={
                        "intent": intent_name,
                        "parsed_intent": parsed_intent,
                        "emotional_state": getattr(self, "current_emo_state", None),
                    },
                )
                ollama_elapsed = time.perf_counter() - ollama_t0
                print(f"Ollama: {ollama_elapsed:.3f}s")

                lowered = (response or "").lower()
                if any(
                    token in lowered
                    for token in [
                        "ollama is not running",
                        "connection was refused",
                        "not running or connection",
                        "timed out",
                        "failed to generate",
                        "failed to",
                        "ollama failed",
                    ]
                ):
                    return "Sorry Faisal, I don't know that yet."
                return response
            else:
                # SKILL execution path
                if plan:
                    response = self.router.execute_plan(plan, text=result.rewritten_query)
                    if response is not None:
                        return response

                response = self.router.route(intent_name, parsed_intent.get("entity"), text=result.rewritten_query)
                if response is not None:
                    return response

        # General / CHAT fallback queries
        if normalized_text.startswith("what is"):
            key = normalized_text.replace("what is", "", 1).strip()
            value = self.memory.recall(key)
            if value:
                return f"{key} is {value}."

        # Greeting shortcuts
        if "hello" in normalized_text or "hi" in normalized_text:
            return f"Hello {OWNER}."

        if "how are you" in normalized_text:
            return "I am doing great."

        if "your name" in normalized_text:
            return f"My name is {NAME}."

        if "bye" in normalized_text:
            return "Goodbye."

        # Execute LLM for general queries
        if not bypass_llm:
            ollama_t0 = time.perf_counter()
            response = self.decision_engine.generate_ai(
                rewritten_text,
                context={
                    "intent": intent_name,
                    "parsed_intent": parsed_intent,
                    "emotional_state": getattr(self, "current_emo_state", None),
                },
            )
            lowered = (response or "").lower()
            if any(
                token in lowered
                for token in [
                    "ollama is not running",
                    "connection was refused",
                    "not running or connection",
                    "timed out",
                    "failed to generate",
                    "failed to",
                    "ollama failed",
                ]
            ):
                return "Sorry Faisal, I don't know that yet."
            return response

        return "Sorry Faisal, I don't know that yet."

    def _record_turn(self, user_input: str, response: str) -> None:
        self.recent_turns.append({"user_input": user_input, "response": response})
        if len(self.recent_turns) > 10:
            self.recent_turns.pop(0)

    def _save_user_name(self, name: str) -> None:
        """Persist the user's name to the memory store."""
        self.memory.remember("name", name, category="personal")

    def _load_saved_name(self) -> Optional[str]:
        """Load the user's name if it has been saved previously."""
        saved_name = self.memory.recall("name")
        if isinstance(saved_name, str):
            return saved_name
        return None
