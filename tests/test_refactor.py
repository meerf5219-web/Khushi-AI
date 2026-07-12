import tempfile
import unittest
from pathlib import Path

from brain.brain import Brain
from brain.intent import IntentEngine
from memory import memory as memory_module
from memory.manager import MemoryManager
from router import Router
from skills.skill_manager import SkillManager


class TestKhushiBehavior(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.original_file_name = memory_module.FILE_NAME
        memory_module.FILE_NAME = str(Path(self.temp_dir.name) / "user_memory.json")

    def tearDown(self) -> None:
        memory_module.FILE_NAME = self.original_file_name

    def test_memory_manager_persists_values(self) -> None:
        manager = MemoryManager()

        manager.remember("city", "London")

        self.assertEqual(manager.recall("city"), "London")

    def test_skill_manager_handles_time_and_app_requests(self) -> None:
        manager = SkillManager()

        time_response = manager.execute("what time is it")
        app_response = manager.execute("open chrome")

        self.assertIsNotNone(time_response)
        self.assertIn("current time", time_response.lower())
        self.assertEqual(app_response, "Opening chrome.")

    def test_brain_handles_remember_command(self) -> None:
        brain = Brain()

        response = brain.think("remember favorite color is blue")

        self.assertTrue(response.startswith("I'll remember that."))
        self.assertEqual(brain.memory.recall("favorite color"), "blue")

    def test_intent_engine_extracts_entities(self) -> None:
        engine = IntentEngine()

        app_intent = engine.detect("open chrome")
        search_intent = engine.detect("search python")
        remember_intent = engine.detect("remember favorite car is ferrari")

        self.assertEqual(app_intent["intent"], "OPEN_APP")
        self.assertEqual(app_intent["entity"], "chrome")
        self.assertEqual(search_intent["intent"], "SEARCH")
        self.assertEqual(search_intent["entity"], "python")
        self.assertEqual(remember_intent["intent"], "REMEMBER")
        self.assertEqual(remember_intent["entity"]["key"], "favorite car")
        self.assertEqual(remember_intent["entity"]["value"], "ferrari")

    def test_router_routes_to_skills(self) -> None:
        brain = Brain()
        router = Router(brain)

        response = router.route("TIME", None, text="what time is it")

        self.assertIn("current time", response.lower())

    def test_brain_remembers_contextual_facts_from_statements(self) -> None:
        brain = Brain()

        response = brain.think("My favourite colour is black")

        self.assertIn("remembered", response.lower())
        self.assertEqual(brain.memory.recall("favourite_colour"), "black")

    def test_brain_recalls_contextual_questions(self) -> None:
        brain = Brain()
        brain.think("I live in Kashmir")

        response = brain.think("Where do I live?")

        self.assertIn("kashmir", response.lower())


if __name__ == "__main__":
    unittest.main()
