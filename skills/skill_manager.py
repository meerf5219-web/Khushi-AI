from typing import Optional

from skills.app_skill import AppSkill
from skills.brightness_skill import BrightnessSkill
from skills.calculator_skill import CalculatorSkill
from skills.clipboard_skill import ClipboardSkill
from skills.date_skill import DateSkill
from skills.file_search_skill import FileSearchSkill
from skills.file_skill import FileSkill
from skills.notes_skill import NotesSkill
from skills.screenshot_skill import ScreenshotSkill
from skills.search_skill import SearchSkill
from skills.search_web_skill import SearchWebSkill
from skills.system_skill import SystemSkill
from skills.time_skill import TimeSkill
from skills.volume_skill import VolumeSkill
from skills.weather_skill import WeatherSkill
from skills.knowledge_skill import KnowledgeSkill


class SkillManager:
    """Route incoming text to the appropriate skill implementation."""

    def __init__(self) -> None:
        self.time = TimeSkill()
        self.date = DateSkill()
        self.app = AppSkill()
        self.search = SearchSkill()
        self.web_search = SearchWebSkill()
        self.system = SystemSkill()
        self.calculator = CalculatorSkill()
        self.weather = WeatherSkill()
        self.knowledge = KnowledgeSkill()
        self.notes = NotesSkill()
        self.file_search = FileSearchSkill()
        self.file = FileSkill()
        self.screenshot = ScreenshotSkill()
        self.clipboard = ClipboardSkill()
        self.volume = VolumeSkill()
        self.brightness = BrightnessSkill()

    def execute(self, text: str) -> Optional[str]:
        """Execute the first matching skill for the provided input."""

        normalized_text = text.lower()

        response = self.system.execute(normalized_text)
        if response:
            return response

        response = self.app.execute(normalized_text)
        if response:
            return response

        response = self.search.execute(normalized_text)
        if response:
            return response

        response = self.calculator.execute(normalized_text)
        if response:
            return response

        response = self.weather.execute(normalized_text)
        if response:
            return response

        if "time" in normalized_text:
            return self.time.execute()

        if "date" in normalized_text:
            return self.date.execute()

        return None