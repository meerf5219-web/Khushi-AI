import sys
from unittest.mock import MagicMock

# Globally mock out heavy modules that cause DLL load failures in CI
# or require specific C++ redistributables that may be missing.

mock_modules = [
    'pywinauto',
    'pyautogui',
    'easyocr',
    'pyperclip',
    'PIL',
    'PIL.Image',
    'mss',
    'cv2',
    'playwright',
    'playwright.sync_api',
    'pyaudio',
    'speech_recognition',
    'pyttsx3'
]

for mod in mock_modules:
    sys.modules[mod] = MagicMock()

# Initialize global QApplication to prevent PySide6 C-level segmentation faults during teardown/collection
try:
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
except Exception:
    pass
