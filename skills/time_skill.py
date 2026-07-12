from datetime import datetime


class TimeSkill:
    """Return the current time in a friendly string."""

    def execute(self) -> str:
        """Return the current time."""
        return datetime.now().strftime("The current time is %I:%M %p")