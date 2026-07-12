import json
import tempfile
import unittest
from pathlib import Path

from skills.calculator_skill import CalculatorSkill
from skills.notes_skill import NotesSkill
from skills.weather_skill import WeatherSkill


class TestSkills(unittest.TestCase):
    def test_calculator_skill_evaluates_common_expressions(self) -> None:
        skill = CalculatorSkill()

        self.assertEqual(skill.execute("2+2"), "4.0")
        self.assertEqual(skill.execute("5*8"), "40.0")
        self.assertEqual(skill.execute("20/4"), "5.0")
        self.assertEqual(skill.execute("(2+3)*4"), "20.0")

    def test_calculator_skill_rejects_unsafe_input(self) -> None:
        skill = CalculatorSkill()

        self.assertEqual(skill.execute("__import__('os').system('echo hi')"), "I could not calculate that.")

    def test_weather_skill_returns_configured_message_when_no_provider(self) -> None:
        skill = WeatherSkill()

        self.assertEqual(skill.execute("weather london"), "Weather service is not configured.")

    def test_notes_skill_persists_and_lists_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            original_path = NotesSkill.__module__
            _ = original_path
            notes_file = Path(temp_dir) / "notes.json"
            import skills.notes_skill as notes_module

            notes_module.NOTES_FILE = str(notes_file)
            skill = NotesSkill()

            self.assertEqual(skill.create_note("take note buy milk"), "Note saved: buy milk")
            self.assertIn("buy milk", skill.show_notes())
            self.assertEqual(skill.delete_notes(), "All notes deleted.")
            self.assertEqual(skill.show_notes(), None)


if __name__ == "__main__":
    unittest.main()
