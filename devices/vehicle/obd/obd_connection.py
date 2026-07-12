import logging
from typing import Dict, Any, List, Optional
from devices.registry import device_registry
from devices.serial.connection import USBSerialConnection

logger = logging.getLogger(__name__)

class OBDConnection:
    """
    OBD-II vehicle interface.
    Validates device registry permissions before allowing sensor readings and diagnostics query.
    """
    def __init__(self, device_id: str = "USB:OBD:ELM327", port: str = "COM3") -> None:
        self.device_id = device_id
        self.port = port
        self.connection = USBSerialConnection(port=port)
        self.is_open = False
        
    def open(self) -> bool:
        """Opens connection to the adapter after validating permissions."""
        if not device_registry.verify_permission(self.device_id, "read_sensors"):
            raise PermissionError(f"Insufficient permissions on device {self.device_id}")
            
        success = self.connection.connect()
        self.is_open = success
        if success:
            # Initialize interface protocol
            self._send_command("ATZ")
            self._send_command("ATE0") # echo off
        return success

    def close(self) -> None:
        self.connection.close()
        self.is_open = False

    def _send_command(self, cmd: str) -> str:
        """Helper to send command over serial and read raw hex response."""
        self.connection.write(cmd.encode("utf-8") + b"\r")
        raw_resp = self.connection.read_until_prompt().decode("utf-8")
        return raw_resp.replace("\r", "").replace("\n", "").replace(">", "").strip()

    def read_sensor(self, pid: str) -> Dict[str, Any]:
        """
        Reads sensor value for a given PID.
        Only allowed if permission is granted.
        """
        if not device_registry.verify_permission(self.device_id, "read_sensors"):
            raise PermissionError("Access denied: missing 'read_sensors' permission.")
            
        if not self.is_open:
            raise ConnectionError("OBD connection is not open.")

        raw = self._send_command(pid)
        # Raw response looks like "41 0C 2E E0"
        tokens = [t for t in raw.split(" ") if t]
        
        # Verify mode echo (response mode should be request mode + 0x40)
        # Request mode is 01, response mode is 41
        if len(tokens) < 3 or tokens[0] != "41":
            return {"status": "error", "message": "Invalid response or no data"}

        # Extract data bytes
        data_bytes = tokens[2:]
        
        # Parse PIDs
        normalized_pid = pid.upper().replace(" ", "")
        if normalized_pid == "010C" and len(data_bytes) >= 2:
            # RPM: (A * 256 + B) / 4
            a, b = int(data_bytes[0], 16), int(data_bytes[1], 16)
            val = (a * 256 + b) / 4.0
            return {"pid": "010C", "sensor": "Engine RPM", "value": val, "unit": "RPM"}
            
        elif normalized_pid == "010D" and len(data_bytes) >= 1:
            # Speed: A
            a = int(data_bytes[0], 16)
            return {"pid": "010D", "sensor": "Vehicle Speed", "value": a, "unit": "km/h"}
            
        elif normalized_pid == "0105" and len(data_bytes) >= 1:
            # Coolant Temp: A - 40
            a = int(data_bytes[0], 16)
            val = a - 40
            return {"pid": "0105", "sensor": "Coolant Temperature", "value": val, "unit": "C"}
            
        elif normalized_pid == "0104" and len(data_bytes) >= 1:
            # Engine Load: A * 100 / 255
            a = int(data_bytes[0], 16)
            val = round((a * 100.0) / 255.0, 1)
            return {"pid": "0104", "sensor": "Engine Load", "value": val, "unit": "%"}
            
        return {"pid": pid, "status": "unknown", "raw": raw}

    def read_diagnostics(self) -> List[str]:
        """
        Reads vehicle trouble codes (DTCs) from ECU memory.
        Requires 'read_diagnostics' permission.
        """
        if not device_registry.verify_permission(self.device_id, "read_diagnostics"):
            raise PermissionError("Access denied: missing 'read_diagnostics' permission.")
            
        if not self.is_open:
            raise ConnectionError("OBD connection is not open.")

        # Request stored trouble codes: Mode 03
        raw = self._send_command("03")
        tokens = [t for t in raw.split(" ") if t]
        
        # Expected response mode 43
        if not tokens or tokens[0] != "43":
            return []

        # Parse DTC codes
        dtcs = []
        # Response structure: 43 [count] [byte1 byte2] [byte3 byte4] ...
        # Every pair of bytes is one DTC code
        data_bytes = tokens[2:]
        
        # Group bytes into pairs
        for i in range(0, len(data_bytes) - 1, 2):
            b1 = data_bytes[i]
            b2 = data_bytes[i+1]
            if b1 == "00" and b2 == "00":
                continue # Null code placeholder
            dtc = self._decode_dtc(b1, b2)
            dtcs.append(dtc)
            
        return dtcs

    def _decode_dtc(self, byte1: str, byte2: str) -> str:
        """Converts two DTC hex bytes to standard diagnostic trouble code format (e.g. P0300)."""
        val = int(byte1 + byte2, 16)
        
        # First 2 bits define category prefix
        first_digit = (val & 0xC000) >> 14
        prefixes = ["P", "C", "B", "U"]
        prefix = prefixes[first_digit]
        
        char2 = (val & 0x3000) >> 12
        char3 = (val & 0x0F00) >> 8
        char4 = (val & 0x00F0) >> 4
        char5 = val & 0x000F
        
        return f"{prefix}{char2:X}{char3:X}{char4:X}{char5:X}"
