import re
import time
from datetime import datetime, timedelta
from typing import Optional

class TimeEngine:
    """Understands natural temporal references."""

    @staticmethod
    def resolve_time(text: str) -> Optional[float]:
        """Convert a natural language time expression to a Unix timestamp."""
        text = text.lower().strip()
        now = datetime.now()
        
        if "today" in text:
            return now.timestamp()
        if "yesterday" in text:
            return (now - timedelta(days=1)).timestamp()
        if "tomorrow" in text:
            return (now + timedelta(days=1)).timestamp()
        if "last week" in text:
            return (now - timedelta(days=7)).timestamp()
        if "next week" in text:
            return (now + timedelta(days=7)).timestamp()
        if "last month" in text:
            return (now - timedelta(days=30)).timestamp()
        if "two days ago" in text:
            return (now - timedelta(days=2)).timestamp()
            
        # Basic mapping for time of day offsets
        if "morning" in text:
            return now.replace(hour=8, minute=0, second=0).timestamp()
        if "afternoon" in text:
            return now.replace(hour=14, minute=0, second=0).timestamp()
        if "evening" in text:
            return now.replace(hour=18, minute=0, second=0).timestamp()
        if "night" in text:
            return now.replace(hour=22, minute=0, second=0).timestamp()

        return None

    @staticmethod
    def relative_time(timestamp: float) -> str:
        """Convert a Unix timestamp into a relative natural language string."""
        delta = datetime.fromtimestamp(timestamp).date() - datetime.now().date()
        days = delta.days
        
        if days == 0:
            return "today"
        elif days == 1:
            return "tomorrow"
        elif days == -1:
            return "yesterday"
        elif days > 1:
            return f"in {days} days"
        else:
            return f"{abs(days)} days ago"

    @staticmethod
    def human_time_description(timestamp: float) -> str:
        """Describe a timestamp in a natural way (e.g., 'yesterday evening')."""
        dt = datetime.fromtimestamp(timestamp)
        relative = TimeEngine.relative_time(timestamp)
        
        hour = dt.hour
        time_of_day = "night"
        if 5 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 17:
            time_of_day = "afternoon"
        elif 17 <= hour < 21:
            time_of_day = "evening"
            
        if relative == "today":
            return f"this {time_of_day}"
        return f"{relative} {time_of_day}"
