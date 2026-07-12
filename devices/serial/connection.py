import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

class USBSerialConnection:
    """
    Abstractions wrapper for USB/Serial communications.
    Interacts with hardware ports, falling back to ELM327 OBD mock responses in testing.
    """
    def __init__(self, port: str = "COM3", baudrate: int = 38400, timeout: float = 1.0) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.is_connected = False
        self.buffer = b""

    def connect(self) -> bool:
        """Establishes connections to the serial port."""
        logger.info(f"Opening serial port {self.port} at {self.baudrate} baud...")
        # In a real environment, self.conn = serial.Serial(self.port, self.baudrate)
        self.is_connected = True
        return True

    def close(self) -> None:
        """Closes serial connections."""
        logger.info(f"Closing serial port {self.port}.")
        self.is_connected = False

    def write(self, data: bytes) -> None:
        """Writes command bytes to the serial connection."""
        if not self.is_connected:
            raise ConnectionError("Serial port is not connected.")
            
        command = data.decode("utf-8").strip().upper().replace(" ", "")
        logger.debug(f"Serial write: {command}")
        
        # Emulate ELM327 microchip reactions
        if command == "ATZ":
            self.buffer += b"ELM327 v1.5\r\n>"
        elif command.startswith("AT"):
            self.buffer += b"OK\r\n>"
        elif command == "010C":
            # RPM PID: Formula (A*256 + B)/4. Let's return 3000 RPM -> (12000) -> 0x2EE0
            self.buffer += b"41 0C 2E E0\r\n>"
        elif command == "010D":
            # Speed PID: A. Let's return 80 km/h -> 0x50
            self.buffer += b"41 0D 50\r\n>"
        elif command == "0105":
            # Coolant Temp PID: A - 40. Let's return 90 C -> 130 -> 0x82
            self.buffer += b"41 05 82\r\n>"
        elif command == "0104":
            # Engine Load PID: A * 100 / 255. Let's return 60% -> 153 -> 0x99
            self.buffer += b"41 04 99\r\n>"
        elif command == "03":
            # Mode 03 DTC request. Return two trouble codes: P0300, P0171
            # Format: 43 (DTC Response) [DTC Count] [DTC1 high/low] [DTC2 high/low]
            # P0300 -> 03 00, P0171 -> 01 71
            self.buffer += b"43 02 03 00 01 71\r\n>"
        else:
            self.buffer += b"NO DATA\r\n>"

    def read_until_prompt(self, timeout_sec: float = 1.0) -> bytes:
        """Reads serial line data until the ELM327 command prompt '>' is encountered."""
        start_time = time.time()
        while time.time() - start_time < timeout_sec:
            if b">" in self.buffer:
                response = self.buffer
                self.buffer = b""
                return response
            time.sleep(0.05)
        raise TimeoutError("Timeout waiting for serial adapter prompt response.")
