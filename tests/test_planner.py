import unittest

from brain.brain import Brain
from planner.planner import Planner


class TestPlanner(unittest.TestCase):
    def test_plan_for_open_and_search(self) -> None:
        planner = Planner()
        plan = planner.plan("Open Chrome and search Python")

        self.assertEqual(len(plan), 2)
        self.assertEqual(plan[0]["intent"], "OPEN_APP")
        self.assertEqual(plan[0]["entity"], "chrome")
        self.assertEqual(plan[1]["intent"], "SEARCH")
        self.assertEqual(plan[1]["entity"], "Python")

    def test_plan_for_open_then_note_creation(self) -> None:
        planner = Planner()
        plan = planner.plan("Open Notepad then create a note")

        self.assertEqual(plan[0]["intent"], "OPEN_APP")
        self.assertEqual(plan[1]["intent"], "NOTE_CREATE")

    def test_plan_for_open_and_time(self) -> None:
        planner = Planner()
        plan = planner.plan("Open Chrome and tell me the time")

        self.assertEqual(plan[0]["intent"], "OPEN_APP")
        self.assertEqual(plan[1]["intent"], "TIME")

    def test_plan_for_open_search_and_screenshot(self) -> None:
        planner = Planner()
        plan = planner.plan("Open Chrome and search Python and take screenshot")

        self.assertEqual(plan[0]["intent"], "OPEN_APP")
        self.assertEqual(plan[1]["intent"], "SEARCH")
        self.assertEqual(plan[2]["intent"], "SCREENSHOT")

    def test_plan_for_notepad_note_and_show_notes(self) -> None:
        planner = Planner()
        plan = planner.plan("Open Notepad and create note and show notes")

        self.assertEqual(plan[0]["intent"], "OPEN_APP")
        self.assertEqual(plan[1]["intent"], "NOTE_CREATE")
        self.assertEqual(plan[2]["intent"], "NOTE_SHOW")

    def test_brain_combines_multiple_step_responses(self) -> None:
        brain = Brain()
        response = brain.think("Open Chrome and tell me the time")

        self.assertIsInstance(response, str)
        self.assertIn("opening chrome", response.lower())
        self.assertIn("current time", response.lower())


if __name__ == "__main__":
    unittest.main()
