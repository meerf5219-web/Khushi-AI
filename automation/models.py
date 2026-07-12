from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

class RiskLevel(Enum):
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()

@dataclass
class AutomationEvent:
    """Represents a structured automation event to be published to the EventBus."""
    action: str
    status: str  # 'Started', 'Completed', 'Failed', 'Cancelled'
    risk_level: RiskLevel
    details: Dict[str, Any]
    error: Optional[str] = None
    duration_ms: Optional[float] = None
