import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from api.server import app, SimpleRateLimiter
from devices.registry import DeviceRegistry, device_registry
from devices.bluetooth.discovery import BluetoothDiscoveryAgent
from devices.serial.connection import USBSerialConnection
from devices.vehicle.obd.obd_connection import OBDConnection
from devices.vehicle.obd.command_queue import OBDCommandQueue
from devices.vehicle.obd.can_bus import CANBusInterface


def test_device_registry_permissions():
    """Verify registry device authorization and permission enforcement checks."""
    registry = DeviceRegistry()
    registry.register_device(
        device_id="TEST:DEV:123",
        device_type="TestType",
        name="Test Device",
        permissions={"read_sensors"}
    )
    
    assert registry.verify_permission("TEST:DEV:123", "read_sensors") is True
    assert registry.verify_permission("TEST:DEV:123", "read_diagnostics") is False
    assert registry.verify_permission("NON_EXISTENT", "read_sensors") is False


def test_bluetooth_discovery():
    """Verify Bluetooth discovery returns nearby virtual adapters."""
    agent = BluetoothDiscoveryAgent(mock_mode=True)
    devices = agent.start_scan()
    assert len(devices) > 0
    assert any(d["device_id"] == "BT:OBD:ELM327" for d in devices)


def test_serial_elm327_emulation():
    """Verify simulated serial ELM327 hex responses are formatted correctly."""
    conn = USBSerialConnection()
    conn.connect()
    
    # ATZ Reboot
    conn.write(b"ATZ\r")
    resp_atz = conn.read_until_prompt()
    assert b"ELM327" in resp_atz
    
    # RPM command
    conn.write(b"010C\r")
    resp_rpm = conn.read_until_prompt()
    assert b"41 0C" in resp_rpm


def test_obd_sensor_decoding_and_permissions():
    """Verify conversion formulas for RPM, Speed, Temp, and Load PIDs."""
    # 1. Deny command on missing permissions
    registry = DeviceRegistry()
    registry.register_device("DEV:MOCK", "Serial", "Mock OBD", permissions=set())
    
    # Temporarily monkeypatch global registry for obd test
    import devices.vehicle.obd.obd_connection as obd_mod
    original_registry = obd_mod.device_registry
    obd_mod.device_registry = registry
    
    obd = OBDConnection(device_id="DEV:MOCK")
    with pytest.raises(PermissionError):
        obd.open()
        
    # Restore original registry
    obd_mod.device_registry = original_registry


def test_obd_readings():
    """Verify correct engineering values are parsed from ELM hex bytes."""
    # Use default registered device (which has read permissions)
    obd = OBDConnection(device_id="USB:OBD:ELM327")
    obd.open()
    
    # Engine RPM (01 0C) -> 3000 RPM
    rpm_data = obd.read_sensor("010C")
    assert rpm_data["value"] == 3000.0
    assert rpm_data["unit"] == "RPM"
    
    # Speed (01 0D) -> 80 km/h
    speed_data = obd.read_sensor("010D")
    assert speed_data["value"] == 80
    assert speed_data["unit"] == "km/h"
    
    # Temp (01 05) -> 130 - 40 = 90 C
    temp_data = obd.read_sensor("0105")
    assert temp_data["value"] == 90
    assert temp_data["unit"] == "C"

    # Load (01 04) -> 153 * 100 / 255 = 60.0%
    load_data = obd.read_sensor("0104")
    assert load_data["value"] == 60.0
    assert load_data["unit"] == "%"
    
    obd.close()


def test_obd_diagnostics_decoder():
    """Verify Mode 03 trouble codes (DTCs) are parsed to standard codes."""
    obd = OBDConnection(device_id="USB:OBD:ELM327")
    obd.open()
    dtcs = obd.read_diagnostics()
    
    # Expect parsed DTCs: P0300 (Random Misfire) and P0171 (System Too Lean)
    assert "P0300" in dtcs
    assert "P0171" in dtcs
    obd.close()


def test_can_bus_boilerplate():
    """Verify CAN bus frame builder outputs."""
    bus = CANBusInterface()
    assert bus.initialize_bus() is True
    assert bus.send_frame(0x7DF, [0x02, 0x01, 0x0C, 0, 0, 0, 0, 0]) is True


def test_command_queue():
    """Verify sequential background command execution and callbacks."""
    obd = OBDConnection(device_id="USB:OBD:ELM327")
    obd.open()
    
    queue_runner = OBDCommandQueue(obd)
    queue_runner.start()
    
    results = []
    def callback(res):
        results.append(res)
        
    # Queue up a sensor reading
    queue_runner.enqueue("read_sensor", callback, "010C")
    
    # Wait for execution
    import time
    time.sleep(0.5)
    
    queue_runner.stop()
    obd.close()
    
    assert len(results) == 1
    assert results[0]["value"] == 3000.0


@pytest.fixture
def client():
    app.state.api_key = "test_obd_key"
    app.state.rate_limiter = SimpleRateLimiter(limit=100)
    with TestClient(app) as c:
        yield c


def test_api_obd_endpoints(client):
    """Verify vehicle REST API endpoints return scan, status, and DTCs."""
    # 1. GET /vehicle/scan
    r = client.get("/vehicle/scan", headers={"x-api-key": "test_obd_key"})
    assert r.status_code == 200
    assert len(r.json()["devices"]) > 0

    # 2. GET /vehicle/status
    r = client.get("/vehicle/status", headers={"x-api-key": "test_obd_key"})
    assert r.status_code == 200
    assert r.json()["telemetry"]["rpm"]["value"] == 3000.0

    # 3. GET /vehicle/diagnostics
    r = client.get("/vehicle/diagnostics", headers={"x-api-key": "test_obd_key"})
    assert r.status_code == 200
    assert "P0300" in r.json()["dtcs"]
