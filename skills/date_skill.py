from datetime import datetime


class DateSkill:
    """Return the current date in a friendly string."""

    def execute(self) -> str:
        """Return the current date."""
        return datetime.now().strftime("Today is %d %B %Y")