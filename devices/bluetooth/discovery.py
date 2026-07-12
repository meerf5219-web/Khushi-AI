import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class BluetoothDiscoveryAgent:
    """
    Scans for local area Bluetooth Classic and BLE devices.
    Returns a virtual device list in test/mock mode.
    """
    def __init__(self, mock_mode: bool = True) -> None:
        self.mock_mode = mock_mode

    def start_scan(self) -> List[Dict[str, Any]]:
        """Scans for nearby Bluetooth devices."""
        logger.info("Starting Bluetooth device discovery scan...")
        if self.mock_mode:
            # Simulated nearby vehicle adapters
            return [
                {
                    "device_id": "BT:OBD:ELM327",
                    "name": "OBDII Bluetooth Link",
                    "rssi": -68,
                    "paired": True
                },
                {
                    "device_id": "BT:AUDIO:MX100",
                    "name": "Sony Headset",
                    "rssi": -55,
                    "paired": False
                }
            ]
            
        try:
            # Fallback to local scans (if bleak / pybluez is ever installed)
            # For safe infrastructure compilation, we use standard library mocks
            return []
        except Exception as e:
            logger.error(f"Bluetooth interface scan error: {e}")
            return []
