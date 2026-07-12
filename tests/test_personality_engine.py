from __future__ import annotations

import unittest
from brain.brain import Brain
from companion.personality.engine import PersonalityEngine


class TestPersonalityEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = PersonalityEngine()

    def test_personality_profile(self) -> None:
        profile = self.engine.enforce_constraints()
        self.assertIn("traits", profile)
        self.assertIn("prohibited", profile)
        self.assertIn("non_emotional", profile)
        self.assertTrue(profile["non_emotional"])
        self.assertTrue(profile["no_emotion_claims"])

    def test_select_tone(self) -> None:
        tone = self.engine.select_tone()
        self.assertIn("Professional", tone)
        self.assertIn("calm", tone)

    def test_consistency_checker_success(self) -> None:
        text = "That is unfortunate. Let's analyze the problem areas and make a plan."
        is_consistent, violations = self.engine.check_consistency(text)
        self.assertTrue(is_consistent)
        self.assertEqual(len(violations), 0)

    def test_consistency_checker_violations(self) -> None:
        # Faking emotions
        is_consistent, violations = self.engine.check_consistency("I feel sad to hear that.")
        self.assertFalse(is_consistent)
        self.assertIn("Faking emotions", violations)

        # Pretending consciousness
        is_consistent, violations = self.engine.check_consistency("I am conscious and have feelings.")
        self.assertFalse(is_consistent)
        self.assertIn("Pretending consciousness", violations)

        # Sarcasm or arrogance
        is_consistent, violations = self.engine.check_consistency("Obviously, you should know that.")
        self.assertFalse(is_consistent)
        self.assertIn("Arrogance or Sarcasm", violations)

        # Overconfidence
        is_consistent, violations = self.engine.check_consistency("I am 100% sure we will win.")
        self.assertFalse(is_consistent)
        self.assertIn("Overconfidence", violations)

    def test_style_controller_sanitization(self) -> None:
        # Faked emotions
        sanitized = self.engine.control_style("I am sorry, I feel sad.", ["Faking emotions"])
        self.assertNotIn("sorry", sanitized.lower())
        self.assertNotIn("feel sad", sanitized.lower())

        # Pretending consciousness
        sanitized = self.engine.control_style("I am conscious and I have feelings.", ["Pretending consciousness"])
        self.assertNotIn("conscious", sanitized.lower())
        self.assertNotIn("feelings", sanitized.lower())

        # Arrogance or sarcasm
        sanitized = self.engine.control_style("Obviously, clearly this is wrong.", ["Arrogance or Sarcasm"])
        self.assertNotIn("obviously", sanitized.lower())
        self.assertNotIn("clearly", sanitized.lower())

        # Overconfidence
        sanitized = self.engine.control_style("I am 100% sure we will win.", ["Overconfidence"])
        self.assertNotIn("100% sure", sanitized.lower())

    def test_brain_integration_sanitization(self) -> None:
        # full Brain think integration check
        brain = Brain()
        
        # Mock/Inject a reply that violates personality rules
        # If the brain returns "Obviously I feel sad and I am sorry", it should be filtered.
        raw_violation = "Obviously I feel sad and I am sorry."
        
        # Test the wrapper directly
        filtered = brain.personality.filter_response(raw_violation)
        self.assertNotIn("obviously", filtered.lower())
        self.assertNotIn("feel sad", filtered.lower())
        self.assertNotIn("sorry", filtered.lower())
