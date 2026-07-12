import os
import sys
import pytest
from unittest.mock import patch, MagicMock


# Skip tests if not on Windows or in CI
pytestmark = pytest.mark.skipif(
    os.name != 'nt' or os.environ.get("CI") == "true",
    reason="Vision automation tests require Windows UI session."
)

@pytest.fixture
def controller():
    from vision.controller import VisionController
    return VisionController()

def test_privacy_mode_blocks_capture(controller):
    """Test that vision capture is blocked when privacy mode is on."""
    controller.privacy_mode = True
    result = controller.analyze_active_window()
    assert "blocked" in result.lower()

def test_disable_privacy_enables_capture(controller):
    """Test that capture runs when privacy mode is explicitly disabled."""
    controller.privacy_mode = False
    with patch.object(controller, '_execute_async') as mock_exec:
        mock_exec.return_value = "worker_123"
        result = controller.analyze_active_window()
        assert result == "worker_123"
        mock_exec.assert_called_once()

@patch('vision.history.HistoryManager.start')
def test_start_history(mock_start, controller):
    """Test enabling continuous capture history."""
    controller.enable_continuous_capture(interval_sec=5)
    assert controller.privacy_mode is False
    mock_start.assert_called_once()

@patch('vision.history.HistoryManager.start')
@patch('vision.history.HistoryManager.stop')
def test_stop_history(mock_stop, mock_start, controller):
    """Test disabling history enforces privacy mode."""
    controller.enable_continuous_capture()
    controller.history.is_running = True
    controller.disable_continuous_capture()
    assert controller.privacy_mode is True
    mock_stop.assert_called_once()
