from __future__ import annotations

import unittest
from brain.brain import Brain
from brain.conversation_pipeline import ConversationPipeline


class TestConversationPipeline(unittest.TestCase):
    def setUp(self) -> None:
        self.brain = Brain()
        self.pipeline = self.brain.conversation_pipeline

    def test_context_stack_management(self) -> None:
        # Push weather topic
        self.pipeline.execute("What is the weather like today?", self.brain)
        self.assertEqual(self.pipeline.active_topic, "weather")
        self.assertIn("weather", self.pipeline.context_stack)

        # Push goals topic
        self.pipeline.execute("Let's review my UPSC study plan goals.", self.brain)
        self.assertEqual(self.pipeline.active_topic, "goals")
        self.assertIn("goals", self.pipeline.context_stack)

        # Pop active topic
        self.pipeline.execute("Actually, cancel topic.", self.brain)
        self.assertEqual(self.pipeline.active_topic, "weather")
        self.assertNotIn("goals", self.pipeline.context_stack)

    def test_conversation_recovery(self) -> None:
        # Push topic
        self.pipeline.execute("Open Chrome for me.", self.brain)
        self.assertEqual(self.pipeline.active_topic, "app_launch")

        # Push another topic
        self.pipeline.execute("Let's look at the weather.", self.brain)
        self.assertEqual(self.pipeline.active_topic, "weather")

        # Recover
        self.pipeline.execute("Actually go back.", self.brain)
        self.assertEqual(self.pipeline.active_topic, "app_launch")

    def test_conversation_summary(self) -> None:
        turns = [
            {"user_input": "What is the weather?", "assistant_output": "Checking weather."},
            {"user_input": "Tell me about my UPSC goals.", "assistant_output": "Here are goals."}
        ]
        summary = self.pipeline.get_summary(turns)
        self.assertIn("weather", summary)
        self.assertIn("UPSC goals", summary)
