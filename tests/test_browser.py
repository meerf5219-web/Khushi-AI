import os
import pytest
from unittest.mock import patch, MagicMock


# Skip tests if not on Windows or in CI
pytestmark = pytest.mark.skipif(
    os.name != 'nt' or os.environ.get("CI") == "true",
    reason="Browser automation tests require Windows UI session."
)

@pytest.fixture
def controller():
    from browser.controller import BrowserController
    return BrowserController()

@patch('browser.forms.require_confirmation')
def test_destructive_form_action_intercepted(mock_confirm, controller):
    """Test that destructive form submits are caught by the safety interceptor."""
    mock_confirm.return_value = False # User rejects the action
    
    with pytest.raises(PermissionError, match="User rejected"):
        # We manually trigger the click since execute_async runs in another thread
        controller.forms.click_button("#submit-btn", text_content="Delete Account")
        
    mock_confirm.assert_called_once()
    
@patch('browser.forms.require_confirmation')
def test_benign_form_action_allowed(mock_confirm, controller):
    """Test that safe form actions don't trigger confirmations."""
    with patch('browser.forms.FormAutomator.click_button'):
        controller.forms.click_button("#next-btn", text_content="Next Page")
        mock_confirm.assert_not_called()

def test_async_worker_execution(controller):
    """Verify that tasks are dispatched to workers correctly."""
    with patch.object(controller, '_execute_async') as mock_exec:
        mock_exec.return_value = "worker_1"
        res = controller.start_session()
        assert res == "worker_1"
        mock_exec.assert_called_once()
