from __future__ import annotations

import unittest
from brain.brain import Brain
from brain.conversation_understanding.engine import NaturalConversationEngine


class TestNaturalConversation(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = NaturalConversationEngine()

    def test_indirect_intent_recognition(self) -> None:
        # App open indirect
        q, resp = self.engine.process_turn("Can you open Chrome?")
        self.assertEqual(q, "open chrome")
        self.assertIsNone(resp)

        # Weather indirect
        q, resp = self.engine.process_turn("Do I need an umbrella today?")
        self.assertEqual(q, "weather today")
        self.assertIsNone(resp)

        # Reminder indirect
        q, resp = self.engine.process_turn("Can you remind me later?")
        self.assertEqual(q, "set a reminder later")
        self.assertIsNone(resp)

    def test_ellipsis_resolution(self) -> None:
        # Seed state with weather in Delhi
        self.engine.state["last_intent"] = "WEATHER"
        self.engine.state["last_location"] = "delhi"
        self.engine.state["last_time"] = "today"

        # Ask "how about tomorrow"
        q, resp = self.engine.process_turn("how about tomorrow?")
        self.assertEqual(q, "weather in delhi tomorrow")

        # Update state city
        self.engine.state["last_time"] = "tomorrow"
        q, resp = self.engine.process_turn("in Mumbai?")
        self.assertEqual(q, "weather in mumbai tomorrow")

    def test_pronoun_resolution(self) -> None:
        # Seed state with last app
        self.engine.state["last_app"] = "notepad"

        # Ask "open it"
        q, resp = self.engine.process_turn("open it")
        self.assertEqual(q, "open notepad")

    def test_conversation_repair(self) -> None:
        # Seed state with incorrect app
        self.engine.state["last_intent"] = "OPEN_APP"
        self.engine.state["last_app"] = "chrome"

        # Say "No, calculator"
        q, resp = self.engine.process_turn("No, calculator")
        self.assertEqual(q, "open calculator")
        self.assertEqual(self.engine.state["last_app"], "calculator")

    def test_natural_acknowledgements(self) -> None:
        q, resp = self.engine.process_turn("thanks, Khushi!")
        self.assertIsNotNone(resp)
        self.assertIn("welcome", resp.lower())

        q, resp = self.engine.process_turn("ok that's it")
        self.assertIsNotNone(resp)
        self.assertIn("understood", resp.lower())

    def test_brain_integration_ellipsis_and_repair(self) -> None:
        # Full end-to-end integration test through Brain
        brain = Brain()
        
        # 1. Ask weather in Delhi
        # (Using a mock or short-circuit query to avoid Ollama dependency)
        resp1 = brain.think("what is the weather in Delhi?")
        self.assertTrue(brain.pipeline.conversation_engine.state["last_location"] == "delhi")
        
        # 2. Ask "how about tomorrow"
        resp2 = brain.think("how about tomorrow?")
        # It should process as weather in Delhi tomorrow
        # (which returns weather skill response or search fallback, but contains delhi/weather/tomorrow or online query)
        self.assertTrue(
            "online" in resp2.lower() or 
            "weather" in resp2.lower() or 
            "delhi" in resp2.lower()
        )

        # 3. Test Repair integration
        resp3 = brain.think("No, Calculator")
        self.assertTrue("calculat" in resp3.lower())
