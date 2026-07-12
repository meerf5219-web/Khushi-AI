import logging
import time
from typing import Any, Dict, Optional
from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QDialogButtonBox
from PySide6.QtCore import Qt, QTimer

from utils.resource_manager import RM
from brain.event_bus import event_bus
from automation.models import RiskLevel, AutomationEvent

# Set up dedicated automation logger
automation_log_path = RM.logs() / "automation.log"
automation_logger = logging.getLogger("automation")
automation_logger.setLevel(logging.INFO)

# Prevent propagating to root logger to avoid mixing with GUI logs
automation_logger.propagate = False 

if not automation_logger.handlers:
    handler = logging.FileHandler(automation_log_path, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    handler.setFormatter(formatter)
    automation_logger.addHandler(handler)

class AutomationConfirmationDialog(QDialog):
    """Reusable dialog for high/critical risk automation actions."""
    def __init__(self, action_desc: str, target: str, risk_level: RiskLevel, timeout_sec: int = 30, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Automation Confirmation Required")
        self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumWidth(400)
        
        self.timeout_sec = timeout_sec
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timeout)
        
        layout = QVBoxLayout(self)
        
        risk_color = "red" if risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH) else "orange"
        
        lbl_risk = QLabel(f"<b style='color:{risk_color};'>Risk Level: {risk_level.name}</b>")
        layout.addWidget(lbl_risk)
        
        lbl_action = QLabel(f"<b>Action:</b> {action_desc}")
        lbl_action.setWordWrap(True)
        layout.addWidget(lbl_action)
        
        lbl_target = QLabel(f"<b>Target:</b> {target}")
        lbl_target.setWordWrap(True)
        layout.addWidget(lbl_target)
        
        self.lbl_timeout = QLabel(f"Auto-rejecting in {self.timeout_sec} seconds...")
        layout.addWidget(self.lbl_timeout)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        
        self.timer.start(1000)

    def _on_timeout(self):
        self.timeout_sec -= 1
        if self.timeout_sec <= 0:
            self.timer.stop()
            self.reject()
        else:
            self.lbl_timeout.setText(f"Auto-rejecting in {self.timeout_sec} seconds...")

def require_confirmation(action_desc: str, target: str, risk_level: RiskLevel, timeout_sec: int = 30) -> bool:
    """Prompt user for confirmation. Used internally by automation logic."""
    if risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM):
        # By default, LOW/MEDIUM don't require explicit popup unless configured otherwise,
        # but the prompt said "All destructive actions must require explicit confirmation."
        # We will assume HIGH/CRITICAL are the ones ALWAYS requiring it.
        # Still, if this function is called, we show the dialog.
        pass
        
    dialog = AutomationConfirmationDialog(action_desc, target, risk_level, timeout_sec)
    result = dialog.exec()
    return result == QDialog.Accepted

def publish_event(action: str, status: str, risk_level: RiskLevel, details: Dict[str, Any], error: Optional[str] = None, duration_ms: Optional[float] = None):
    """Log to automation.log and publish to EventBus."""
    event = AutomationEvent(action=action, status=status, risk_level=risk_level, details=details, error=error, duration_ms=duration_ms)
    
    # Log to file
    log_msg = f"Action={action} Status={status} Risk={risk_level.name} Details={details}"
    if error:
        log_msg += f" Error={error}"
    if duration_ms is not None:
        log_msg += f" Duration={duration_ms:.2f}ms"
        
    if status == 'Failed':
        automation_logger.error(log_msg)
    else:
        automation_logger.info(log_msg)
        
    # Publish to EventBus
    # EventBus topics are strings. Let's use 'automation'
    event_bus.publish('automation', event)
