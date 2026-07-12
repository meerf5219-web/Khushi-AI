import pyautogui
import pyperclip

class KeyboardAutomation:
    """Manages keyboard operations."""
    
    def type_text(self, text: str, interval: float = 0.05) -> None:
        """Type a string of text with a small delay between keystrokes."""
        pyautogui.typewrite(text, interval=interval)

    def press(self, key: str) -> None:
        """Press a single key."""
        pyautogui.press(key)

    def hotkey(self, *keys) -> None:
        """Press a combination of keys (e.g. 'ctrl', 'c')."""
        pyautogui.hotkey(*keys)

    def copy_to_clipboard(self, text: str) -> None:
        """Set clipboard text."""
        pyperclip.copy(text)

    def paste_from_clipboard(self) -> str:
        """Get clipboard text."""
        return pyperclip.paste()
