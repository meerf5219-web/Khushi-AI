from __future__ import annotations

import unittest
from brain.emotional_intelligence.engine import EmotionalIntelligenceEngine, EmotionalState


class TestEmotionalIntelligence(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = EmotionalIntelligenceEngine()

    def test_sadness_detection(self) -> None:
        state = self.engine.analyze_text("I failed my exam, this is the worst day ever.")
        self.assertEqual(state.primary_emotion, "sadness")
        self.assertTrue(state.intensity > 0.5)
        self.assertIn("failed", state.detected_keywords)
        self.assertIn("worst", state.detected_keywords)

    def test_stress_detection(self) -> None:
        state = self.engine.analyze_text("I am extremely overwhelmed and anxious under all this pressure.")
        self.assertEqual(state.primary_emotion, "stress")
        self.assertTrue(state.stress > 0.6)
        self.assertIn("overwhelmed", state.detected_keywords)
        self.assertIn("anxious", state.detected_keywords)

    def test_frustration_detection(self) -> None:
        state = self.engine.analyze_text("I am stuck on this coding problem. It is annoying and I cannot do this.")
        self.assertEqual(state.primary_emotion, "frustration")
        self.assertTrue(state.frustration > 0.6)
        self.assertIn("stuck", state.detected_keywords)
        self.assertIn("annoying", state.detected_keywords)

    def test_motivation_detection(self) -> None:
        state = self.engine.analyze_text("I feel ready and focused, I will win and crack my goals.")
        self.assertEqual(state.primary_emotion, "motivation")
        self.assertTrue(state.motivation > 0.5)
        self.assertTrue(state.confidence > 0.5)

    def test_celebration_detection(self) -> None:
        state = self.engine.analyze_text("Yes! I passed the test! This is amazing news!")
        self.assertEqual(state.primary_emotion, "celebration")
        self.assertTrue(state.celebration > 0.6)
        self.assertIn("passed", state.detected_keywords)

    def test_burnout_detection(self) -> None:
        state = self.engine.analyze_text("I am so tired and exhausted. I feel burned out and need rest.")
        self.assertEqual(state.primary_emotion, "burnout")
        self.assertTrue(state.burnout > 0.6)
        self.assertIn("tired", state.detected_keywords)
        self.assertIn("exhausted", state.detected_keywords)

    def test_confidence_estimation(self) -> None:
        state_high = self.engine.analyze_text("I am confident and sure I got this.")
        self.assertTrue(state_high.confidence > 0.7)

        state_low = self.engine.analyze_text("I am unsure and doubt my work.")
        self.assertTrue(state_low.confidence < 0.5)

    def test_response_personalization_sadness_with_goal(self) -> None:
        state = self.engine.analyze_text("I failed my exam.")
        profile_data = {
            "goals": {
                "goals:upsc": {
                    "payload": {"value": "Crack UPSC"}
                }
            }
        }
        response = self.engine.personalize_response(state, "I failed my exam.", profile_data)
        self.assertIsNotNone(response)
        self.assertIn("Crack UPSC", response)
        self.assertNotIn("I feel", response)
        self.assertNotIn("I am sad", response)
        self.assertNotIn("I love you", response)

    def test_response_personalization_burnout_with_project(self) -> None:
        state = self.engine.analyze_text("I am so burnt out.")
        profile_data = {
            "projects": {
                "projects:khushi": {
                    "payload": {"value": "Khushi AI"}
                }
            }
        }
        response = self.engine.personalize_response(state, "I am so burnt out.", profile_data)
        self.assertIsNotNone(response)
        self.assertIn("Khushi AI", response)
        self.assertIn("structured pause", response)

    def test_response_personalization_neutral(self) -> None:
        state = self.engine.analyze_text("What time is it?")
        self.assertEqual(state.primary_emotion, "neutral")
        response = self.engine.personalize_response(state, "What time is it?", {})
        self.assertIsNone(response)

    def test_brain_think_emotional_personalization_sadness(self) -> None:
        from brain.brain import Brain
        from memory.companion.engine import MemoryRecord
        
        brain = Brain()
        
        # Manually seed a goal in companion memory store
        brain.cie._store.upsert_record(
            bucket="goals",
            record_id="goals:upsc",
            record=MemoryRecord(
                created_date="2026-07-01T10:00:00Z",
                updated_date="2026-07-01T10:00:00Z",
                confidence=1.0,
                source="user",
                category="goals",
                payload={"value": "Crack UPSC", "id": "goals:upsc"}
            )
        )
        
        response = brain.think("I failed my exam.")
        self.assertIn("Crack UPSC", response)
        self.assertNotIn("I feel", response)
        self.assertNotIn("I am sad", response)
        self.assertNotIn("I love you", response)

    def test_brain_think_emotional_personalization_burnout(self) -> None:
        from brain.brain import Brain
        from memory.companion.engine import MemoryRecord
        
        brain = Brain()
        
        # Manually seed a project in companion memory store
        brain.cie._store.upsert_record(
            bucket="projects",
            record_id="projects:khushi",
            record=MemoryRecord(
                created_date="2026-07-01T10:00:00Z",
                updated_date="2026-07-01T10:00:00Z",
                confidence=1.0,
                source="user",
                category="projects",
                payload={"value": "Khushi AI", "id": "projects:khushi"}
            )
        )
        
        response = brain.think("I am extremely exhausted and burnt out.")
        self.assertIn("Khushi AI", response)
        self.assertIn("structured pause", response)
        self.assertNotIn("I feel", response)
        self.assertNotIn("I am sad", response)
