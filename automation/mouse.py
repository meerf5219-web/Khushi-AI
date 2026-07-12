import pyautogui
from typing import Tuple

class MouseAutomation:
    """Manages mouse operations."""
    
    def move(self, x: int, y: int, duration: float = 0.25) -> None:
        """Move cursor to absolute coordinates."""
        pyautogui.moveTo(x, y, duration=duration)

    def click(self, button: str = 'left', clicks: int = 1) -> None:
        """Click the mouse."""
        pyautogui.click(button=button, clicks=clicks)

    def double_click(self) -> None:
        """Double left-click."""
        pyautogui.doubleClick()

    def right_click(self) -> None:
        """Right click."""
        pyautogui.rightClick()

    def scroll(self, clicks: int) -> None:
        """Scroll mouse wheel."""
        pyautogui.scroll(clicks)

    def drag_and_drop(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5) -> None:
        """Drag from start to end."""
        pyautogui.moveTo(start_x, start_y)
        pyautogui.dragTo(end_x, end_y, duration=duration, button='left')
        
    def get_position(self) -> Tuple[int, int]:
        """Get current mouse position."""
        return pyautogui.position()
