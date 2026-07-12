import unittest

from brain.brain import Brain


class TestRoutingAudit(unittest.TestCase):
    def test_brain_routes_calculation_and_weather(self) -> None:
        brain = Brain()

        calculate_response = brain.think("what is 2+2")
        weather_response = brain.think("weather in Delhi")

        self.assertNotEqual(calculate_response, "Sorry Faisal, I don't know that yet.")
        self.assertNotEqual(weather_response, "Sorry Faisal, I don't know that yet.")

    def test_brain_routes_notes_and_system_requests(self) -> None:
        brain = Brain()

        note_response = brain.think("take note milk")
        system_response = brain.think("battery")
        search_response = brain.think("search python")
        goodbye_response = brain.think("goodbye")

        self.assertNotEqual(note_response, "Sorry Faisal, I don't know that yet.")
        self.assertNotEqual(system_response, "Sorry Faisal, I don't know that yet.")
        self.assertNotEqual(search_response, "Sorry Faisal, I don't know that yet.")
        self.assertTrue(goodbye_response.startswith("Goodbye."))


if __name__ == "__main__":
    unittest.main()
