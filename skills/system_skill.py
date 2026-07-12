import importlib
import logging
import os
import platform
import time
from typing import Optional


def _load_optional_module(module_name: str):
    """Import an optional dependency lazily without failing the module import."""
    try:
        return importlib.import_module(module_name)
    except ImportError:  # pragma: no cover - optional dependency
        return None


pyautogui = _load_optional_module("pyautogui")
keyboard = _load_optional_module("keyboard")
ctypes = _load_optional_module("ctypes")
psutil = _load_optional_module("psutil")

from utils.resource_manager import RM

logger = logging.getLogger(__name__)


def _screenshot_dir() -> str:
    d = RM.screenshots()
    d.mkdir(parents=True, exist_ok=True)
    return str(d)


class SystemSkill:
    """Provide basic system monitoring and desktop-control responses."""

    def execute(self, text: str) -> Optional[str]:
        """Return a system-related response when the input matches."""
        logger.info("SystemSkill executed with text: %s", text)
        normalized_text = text.lower()

        if self._is_screenshot_request(normalized_text):
            return self.take_screenshot()

        if "volume up" in normalized_text or "increase volume" in normalized_text:
            return self.volume_up()

        if "volume down" in normalized_text or "decrease volume" in normalized_text:
            return self.volume_down()

        if "mute" in normalized_text:
            return self.mute()

        if "lock computer" in normalized_text or "lock pc" in normalized_text:
            return self.lock_pc()

        if "show desktop" in normalized_text:
            return self.show_desktop()

        if "battery" in normalized_text:
            if psutil is None:
                return "Battery information is unavailable."
            battery = psutil.sensors_battery()
            if battery:
                return f"Battery is {battery.percent} percent."

            return "Battery information is unavailable."

        if "cpu" in normalized_text or "cpu usage" in normalized_text:
            if psutil is None:
                return "CPU information is unavailable."
            return f"CPU usage is {psutil.cpu_percent(interval=None)} percent."

        if "ram" in normalized_text or "memory usage" in normalized_text:
            if psutil is None:
                return "RAM information is unavailable."
            ram = psutil.virtual_memory()
            return f"RAM usage is {ram.percent} percent."

        if "disk" in normalized_text:
            if psutil is None:
                return "Disk information is unavailable."
            disk = psutil.disk_usage("/")
            return f"Disk usage is {disk.percent} percent."

        if "uptime" in normalized_text:
            if psutil is None:
                return "Uptime information is unavailable."
            return f"System uptime is {int(psutil.boot_time())} seconds."

        if "computer name" in normalized_text:
            return platform.node()

        return None

    def take_screenshot(self) -> str:
        """Capture a screenshot and save it under the screenshots directory."""
        logger.info("Taking screenshot")
        if pyautogui is None:
            return "Screenshot support is unavailable."

        screenshot_dir = _screenshot_dir()
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(screenshot_dir, f"screenshot_{timestamp}.png")

        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
        except Exception as exc:  # pragma: no cover - runtime dependency
            logger.exception("Screenshot capture failed: %s", exc)
            return str(exc)

        return "Screenshot saved successfully."

    def volume_up(self) -> str:
        """Increase the system volume when supported."""
        logger.info("Increasing volume")
        if pyautogui is not None:
            try:
                pyautogui.press("volumeup")
                return "Volume increased."
            except Exception as exc:  # pragma: no cover - runtime dependency
                logger.warning("Volume up failed: %s", exc)

        return "Volume control is unavailable."

    def volume_down(self) -> str:
        """Decrease the system volume when supported."""
        logger.info("Decreasing volume")
        if pyautogui is not None:
            try:
                pyautogui.press("volumedown")
                return "Volume decreased."
            except Exception as exc:  # pragma: no cover - runtime dependency
                logger.warning("Volume down failed: %s", exc)

        return "Volume control is unavailable."

    def mute(self) -> str:
        """Mute the system volume when supported."""
        logger.info("Muting volume")
        if pyautogui is not None:
            try:
                pyautogui.press("volumemute")
                return "Volume muted."
            except Exception as exc:  # pragma: no cover - runtime dependency
                logger.warning("Mute failed: %s", exc)

        return "Volume control is unavailable."

    def lock_pc(self) -> str:
        """Lock the workstation on Windows systems."""
        logger.info("Locking workstation")
        if ctypes is None:
            return "Locking is unavailable on this system."

        try:
            ctypes.windll.user32.LockWorkStation()
            return "Computer locked."
        except Exception as exc:  # pragma: no cover - runtime dependency
            logger.warning("Locking failed: %s", exc)
            return "I could not lock the computer."

    def show_desktop(self) -> str:
        """Show the desktop using the available desktop shortcut."""
        logger.info("Showing desktop")
        if pyautogui is not None:
            try:
                pyautogui.hotkey("win", "d")
                return "Showing desktop."
            except Exception as exc:  # pragma: no cover - runtime dependency
                logger.warning("Show desktop failed: %s", exc)

        if keyboard is not None:
            try:
                keyboard.press_and_release("win+d")
                return "Showing desktop."
            except Exception as exc:  # pragma: no cover - runtime dependency
                logger.warning("Show desktop failed: %s", exc)

        return "Show desktop is unavailable on this system."

    def _is_screenshot_request(self, text: str) -> bool:
        """Check whether the input requests a screenshot."""
        return "screenshot" in text or "capture screen" in text or "capture" in text