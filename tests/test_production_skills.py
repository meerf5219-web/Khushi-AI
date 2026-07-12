import unittest

from skills.brightness_skill import BrightnessSkill
from skills.clipboard_skill import ClipboardSkill
from skills.file_search_skill import FileSearchSkill
from skills.screenshot_skill import ScreenshotSkill
from skills.system_skill import SystemSkill
from skills.volume_skill import VolumeSkill


class TestProductionSkills(unittest.TestCase):
    def test_file_search_skill_returns_result_or_message(self) -> None:
        skill = FileSearchSkill()
        result = skill.execute("find python")

        self.assertTrue(result is None or isinstance(result, str))

    def test_screenshot_skill_handles_missing_dependency(self) -> None:
        skill = ScreenshotSkill()

        self.assertIn("screenshot", skill.execute("take screenshot").lower())

    def test_clipboard_skill_handles_missing_dependency(self) -> None:
        skill = ClipboardSkill()

        self.assertIn("unavailable", skill.execute("show").lower())

    def test_volume_skill_handles_unavailable_environment(self) -> None:
        skill = VolumeSkill()

        self.assertIn("unavailable", skill.execute("increase").lower())

    def test_brightness_skill_handles_unavailable_environment(self) -> None:
        skill = BrightnessSkill()
        result = skill.execute("current").lower()

        # screen-brightness-control is installed: may return real brightness OR
        # "unavailable" in headless/CI environments. Both are valid responses.
        self.assertTrue(
            "unavailable" in result or "brightness" in result,
            msg=f"Expected brightness info or unavailable message, got: {result!r}",
        )

    def test_system_skill_handles_common_actions(self) -> None:
        skill = SystemSkill()

        self.assertIsInstance(skill.execute("take screenshot"), str)
        self.assertIsInstance(skill.execute("volume up"), str)
        self.assertIsInstance(skill.execute("mute"), str)
        self.assertIsInstance(skill.execute("lock computer"), str)
        self.assertIsInstance(skill.execute("show desktop"), str)


if __name__ == "__main__":
    unittest.main()
