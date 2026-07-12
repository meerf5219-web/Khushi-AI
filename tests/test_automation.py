import os
import sys
import pytest
from unittest.mock import patch, MagicMock


from automation.models import RiskLevel
from automation.utils import require_confirmation

@pytest.fixture
def controller():
    from automation.controller import AutomationController
    return AutomationController()

@patch('automation.filesystem.require_confirmation')
@patch('shutil.rmtree')
@patch('os.remove')
@patch('os.path.exists')
@patch('os.path.getsize')
@patch('os.path.getmtime')
def test_filesystem_delete_confirmation(mock_getmtime, mock_getsize, mock_exists, mock_remove, mock_rmtree, mock_confirm, controller):
    """Test that deleting a file requests confirmation."""
    mock_exists.return_value = True
    mock_getsize.return_value = 100
    mock_getmtime.return_value = 1600000000.0
    mock_confirm.return_value = False  # User clicks 'No'
    
    with pytest.raises(PermissionError):
        controller.fs.delete("C:\\fake\\path.txt")
        
    mock_confirm.assert_called_once()
    mock_remove.assert_not_called()

@patch('automation.system.require_confirmation')
@patch('os.system')
def test_system_shutdown_confirmation(mock_system, mock_confirm, controller):
    """Test that shutdown requests confirmation."""
    mock_confirm.return_value = False  # User clicks 'No'
    
    with pytest.raises(PermissionError):
        controller.system.shutdown()
        
    mock_confirm.assert_called_once()
    mock_system.assert_not_called()

def test_mouse_move(controller):
    """Test mouse move integration."""
    with patch('pyautogui.moveTo') as mock_moveTo:
        controller.mouse.move(100, 100, duration=0.1)
        mock_moveTo.assert_called_once_with(100, 100, duration=0.1)

def test_keyboard_type(controller):
    """Test keyboard typing integration."""
    with patch('pyautogui.typewrite') as mock_typewrite:
        controller.keyboard.type_text("Hello", interval=0.01)
        mock_typewrite.assert_called_once_with("Hello", interval=0.01)

def test_ocr_extract(controller):
    """Test OCR text extraction mock."""
    with patch('automation.ocr_engine.EasyOCREngine') as mock_easyocr_class:
        mock_instance = mock_easyocr_class.return_value
        mock_instance.extract_text.return_value = ("Test text", [])
        
        controller.ocr.engine = mock_instance
        with patch('automation.ocr.OCRAutomation.capture_screen') as mock_capture:
            mock_capture.return_value = MagicMock() # Mock Image
            with patch('PIL.Image.Image.save'):
                text, bboxes = controller.ocr.extract_text()
                assert text == "Test text"
