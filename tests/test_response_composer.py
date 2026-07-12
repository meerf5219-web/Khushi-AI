from __future__ import annotations

import unittest
from brain.emotional_intelligence.engine import EmotionalState
from brain.response_composer.engine import ResponseComposer
from memory.companion.engine import MemoryRecord


class TestResponseComposer(unittest.TestCase):
    def setUp(self) -> None:
        self.composer = ResponseComposer()

    def test_empathy_addition(self) -> None:
        # Sadness state
        state = EmotionalState(
            primary_emotion="sadness",
            intensity=0.8,
            stress=0.0,
            frustration=0.0,
            motivation=0.0,
            celebration=0.0,
            burnout=0.0,
            confidence=0.5,
            detected_keywords=[]
        )
        composed = self.composer.compose("The test scores are low.", state)
        self.assertIn("difficult", composed)
        self.assertIn("The test scores are low.", composed)

        # Stress state
        state_stress = EmotionalState(
            primary_emotion="neutral",
            intensity=0.0,
            stress=0.7,
            frustration=0.0,
            motivation=0.0,
            celebration=0.0,
            burnout=0.0,
            confidence=0.5,
            detected_keywords=[]
        )
        composed_stress = self.composer.compose("I have too many assignments.", state_stress)
        self.assertIn("high demand", composed_stress)

    def test_shortening_response(self) -> None:
        style = "User Interaction Preferences:\n- Answer in a brief, concise, and direct manner."
        long_text = "This is the first sentence. This is the second sentence. This is the third sentence. This is the fourth sentence that should be removed."
        composed = self.composer.compose(long_text, style_instructions=style)
        self.assertNotIn("fourth sentence", composed)
        self.assertIn("first sentence", composed)

    def test_structured_list_formatting(self) -> None:
        style = "User Interaction Preferences:\n- Format response using structured lists and bullet points."
        text = "First task is reading. Second task is writing. Third task is coding."
        # This will be formatted using list styles
        composed = self.composer.compose(text, style_instructions=style)
        self.assertTrue("First task is reading" in composed)
        self.assertTrue("•" in composed or "\u2022" in composed)

    def test_hallucination_prevention(self) -> None:
        # Mock profile without "Paris"
        profile_data = {
            "identity": {
                "name": {
                    "payload": {"value": "Faisal"}
                }
            }
        }
        text = "I remember you told me you lived in Paris."
        composed = self.composer.compose(text, profile_data=profile_data)
        # Should detect "lived in Paris" is not in memory and omit/sanitize the sentence
        self.assertNotIn("Paris", composed)
        self.assertIn("programmed to assist", composed)

        # If "Paris" is in memory, it should NOT omit it
        profile_data_ok = {
            "identity": {
                "name": {
                    "payload": {"value": "Faisal"}
                },
                "location": {
                    "payload": {"value": "lived in Paris"}
                }
            }
        }
        composed_ok = self.composer.compose(text, profile_data=profile_data_ok)
        self.assertIn("Paris", composed_ok)
