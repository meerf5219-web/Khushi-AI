from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from brain.interaction_preferences.engine import InteractionPreferenceEngine
from memory.companion.engine import CompanionMemoryStore


class TestInteractionPreferences(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        
        self.db_file = str(Path(self.temp_dir.name) / "companion_memory.json")
        self.store = CompanionMemoryStore(file_name=self.db_file)
        self.engine = InteractionPreferenceEngine()

    def test_learn_explanation_length(self) -> None:
        # Test learning detailed
        res = self.engine.analyze_and_update("Could you do a deep dive on this subject?", self.store)
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "explanation_length")
        self.assertEqual(res[1], "detailed")

        # Test learning short
        res_short = self.engine.analyze_and_update("Just keep it short.", self.store)
        self.assertIsNotNone(res_short)
        self.assertEqual(res_short[0], "explanation_length")
        self.assertEqual(res_short[1], "short")

        # Check stored value
        summary = self.store.get_summary()
        records = summary.get("preferences", {}).get("records", {})
        self.assertIn("preferences:explanation_length", records)

    def test_learn_communication_style(self) -> None:
        # Test list formatting
        res = self.engine.analyze_and_update("Please use bullet points for the notes.", self.store)
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "communication_style")
        self.assertEqual(res[1], "structured")

    def test_learn_coding_style(self) -> None:
        # Test clean code preference
        res = self.engine.analyze_and_update("I prefer clean code structure.", self.store)
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "coding_style")
        self.assertEqual(res[1], "clean code")

    def test_sensitive_attributes_skipped(self) -> None:
        # Sensitive attributes should NOT be parsed or stored
        res = self.engine.analyze_and_update("This is my private medical secret study routine.", self.store)
        self.assertIsNone(res)

        summary = self.store.get_summary()
        records = summary.get("preferences", {}).get("records", {})
        self.assertEqual(len(records), 0)

    def test_get_style_instructions(self) -> None:
        # Learn short explanation length and list formatting
        self.engine.analyze_and_update("concise brief summary please.", self.store)
        self.engine.analyze_and_update("format in bullet points.", self.store)

        instructions = self.engine.get_style_instructions(self.store)
        self.assertIn("brief, concise, and direct", instructions)
        self.assertIn("structured lists and bullet points", instructions)
