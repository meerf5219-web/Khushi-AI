import logging
from typing import Dict, List, Set, Any, Optional

logger = logging.getLogger(__name__)

class DeviceRegistry:
    """
    Registry for connected smart devices and vehicles.
    Implements a strict permission checking model to ensure safe read-only operations.
    """
    def __init__(self) -> None:
        # device_id -> {"type": str, "name": str, "permissions": Set[str], "status": str}
        self.registry: Dict[str, Dict[str, Any]] = {}
        # Seed default permitted mock virtual ELM327 adapter
        self.register_device(
            device_id="USB:OBD:ELM327",
            device_type="Serial",
            name="Virtual OBD-II ELM327 USB Adapter",
            permissions={"read_sensors", "read_diagnostics"}
        )
        self.register_device(
            device_id="BT:OBD:ELM327",
            device_type="Bluetooth",
            name="Virtual OBD-II ELM327 Bluetooth Adapter",
            permissions={"read_sensors", "read_diagnostics"}
        )

    def register_device(self, device_id: str, device_type: str, name: str, permissions: Set[str]) -> None:
        """Register a new device with explicitly granted permissions."""
        self.registry[device_id] = {
            "type": device_type,
            "name": name,
            "permissions": set(permissions),
            "status": "Registered"
        }
        logger.info(f"Device registered: {device_id} ({name}) with permissions: {permissions}")

    def unregister_device(self, device_id: str) -> None:
        """Remove a device from the registry."""
        if device_id in self.registry:
            del self.registry[device_id]
            logger.info(f"Device unregistered: {device_id}")

    def verify_permission(self, device_id: str, permission: str) -> bool:
        """Verifies if the specified device has been granted a specific action permission."""
        device = self.registry.get(device_id)
        if not device:
            logger.warning(f"Access denied: device {device_id} is not registered.")
            return False
            
        granted = permission in device.get("permissions", set())
        if not granted:
            logger.warning(f"Access denied: device {device_id} does not have '{permission}' permission.")
        return granted

    def list_devices(self) -> List[Dict[str, Any]]:
        """Returns all registered devices and their metadata."""
        devices = []
        for d_id, data in self.registry.items():
            devices.append({
                "device_id": d_id,
                "type": data["type"],
                "name": data["name"],
                "permissions": list(data["permissions"]),
                "status": data["status"]
            })
        return devices


# Global device registry singleton
device_registry = DeviceRegistry()
