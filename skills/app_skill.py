import logging
import os
import webbrowser
from typing import Optional

logger = logging.getLogger(__name__)


class AppSkill:
    """Launch common desktop applications when requested."""

    def open_url(self, url: str) -> Optional[str]:
        """Open a web page in the default browser."""
        normalized_url = url.strip()
        if not normalized_url:
            return None

        try:
            webbrowser.open(normalized_url if normalized_url.startswith("http") else f"https://{normalized_url}")
        except webbrowser.Error as exc:
            logger.warning("Unable to open URL %s: %s", normalized_url, exc)
            return None

        return f"Opening {normalized_url}."

    def execute(self, text: str) -> Optional[str]:
        """Open a known application if it appears in the input text."""
        normalized_text = text.lower()

        apps = {
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
        }

        for app, path in apps.items():
            if app in normalized_text:
                try:
                    os.startfile(path)
                except (AttributeError, FileNotFoundError, OSError) as exc:
                    logger.warning("Unable to launch %s: %s", app, exc)
                return f"Opening {app}."

        return None