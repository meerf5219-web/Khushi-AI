import asyncio
import io
import time
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from fastapi import WebSocketDisconnect

from api.server import app, SimpleRateLimiter
from brain.event_bus import event_bus


@pytest.fixture
def mock_brain():
    brain = MagicMock()
    brain.think.return_value = "Voice executed."
    brain.memory.recall.return_value = "blue"
    
    # Mock companion engine and store
    brain.cie = MagicMock()
    brain.cie._store = MagicMock()
    brain.cie._store.get_summary.return_value = {
        "identity": {"records": {}},
        "goals": {"records": {}},
        "projects": {"records": {}},
        "timeline": {"records": []}
    }
    return brain


@pytest.fixture
def client(mock_brain, monkeypatch):
    app.state.brain = mock_brain
    app.state.api_key = "test_mobile_secret"
    app.state.rate_limiter = SimpleRateLimiter(limit=100)
    
    mock_db = {"tasks": {"task1": "Buy milk"}}
    import memory.memory
    monkeypatch.setattr(memory.memory, "load_memory", lambda: mock_db)
    monkeypatch.setattr(memory.memory, "save_memory", lambda data: mock_db.update(data))
    
    with TestClient(app) as c:
        yield c


def test_api_pairing(client):
    """Verify pairing checks API status and returns platform details."""
    r = client.get("/api/pair", headers={"x-api-key": "test_mobile_secret"})
    assert r.status_code == 200
    assert r.json()["status"] == "paired"
    assert "desktop_name" in r.json()


def test_task_sync(client):
    """Verify listing, saving, and deleting tasks."""
    # 1. GET /tasks
    r = client.get("/tasks", headers={"x-api-key": "test_mobile_secret"})
    assert r.status_code == 200
    assert "tasks" in r.json()

    # 2. POST /tasks
    r = client.post(
        "/tasks",
        json={"key": "task1", "value": "Buy milk", "category": "tasks"},
        headers={"x-api-key": "test_mobile_secret"}
    )
    assert r.status_code == 200

    # 3. DELETE /tasks
    r = client.delete("/tasks/task1", headers={"x-api-key": "test_mobile_secret"})
    assert r.status_code == 200
    assert r.json()["status"] == "success"


def test_media_uploads(client):
    """Verify file uploads for camera and screenshots, and desktop screenshot download."""
    # Camera Upload
    camera_file = io.BytesIO(b"camera_data")
    r = client.post(
        "/upload/camera",
        files={"file": ("photo.jpg", camera_file, "image/jpeg")},
        headers={"x-api-key": "test_mobile_secret"}
    )
    assert r.status_code == 200
    assert r.json()["status"] == "success"

    # Screenshot Upload
    screenshot_file = io.BytesIO(b"screenshot_data")
    r = client.post(
        "/upload/screenshot",
        files={"file": ("screen.jpg", screenshot_file, "image/jpeg")},
        headers={"x-api-key": "test_mobile_secret"}
    )
    assert r.status_code == 200
    assert r.json()["status"] == "success"

    # GET Desktop Screenshot
    r = client.get("/desktop/screenshot", headers={"x-api-key": "test_mobile_secret"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"


def test_clipboard_endpoints(client):
    """Verify remote clipboard reading and writing."""
    # Write clipboard text
    r = client.post(
        "/clipboard",
        json={"text": "Hello Clipboard"},
        headers={"x-api-key": "test_mobile_secret"}
    )
    assert r.status_code == 200
    assert r.json() == {"status": "success"}

    # Read clipboard text
    r = client.get("/clipboard", headers={"x-api-key": "test_mobile_secret"})
    assert r.status_code == 200
    assert "text" in r.json()


def test_file_transfer(client):
    """Verify listing, uploading, and downloading shared files."""
    # Upload file
    test_file = io.BytesIO(b"file_contents")
    r = client.post(
        "/files/upload",
        files={"file": ("test.txt", test_file, "text/plain")},
        headers={"x-api-key": "test_mobile_secret"}
    )
    assert r.status_code == 200
    assert r.json()["status"] == "success"

    # List files
    r = client.get("/files", headers={"x-api-key": "test_mobile_secret"})
    assert r.status_code == 200
    assert "test.txt" in r.json()["files"]

    # Download file
    r = client.get("/files/download/test.txt", headers={"x-api-key": "test_mobile_secret"})
    assert r.status_code == 200
    assert r.content == b"file_contents"


def test_remote_voice(client):
    """Verify sending a voice audio clip for processing."""
    voice_file = io.BytesIO(b"voice_data")
    r = client.post(
        "/voice/remote",
        files={"file": ("speech.wav", voice_file, "audio/wav")},
        headers={"x-api-key": "test_mobile_secret"}
    )
    assert r.status_code == 200
    assert "text" in r.json()
    assert "response" in r.json()


def test_websocket_events(client):
    """Verify real-time desktop event notifications stream over WebSocket."""
    with client.websocket_connect("/events?token=test_mobile_secret") as ws:
        # Publish an event to the EventBus
        event_bus.publish("MEMORY_UPDATED", {"key": "color", "value": "red"})

        # Receive pushed event
        msg = ws.receive_json()
        assert msg["topic"] == "MEMORY_UPDATED"
        assert msg["data"] == {"key": "color", "value": "red"}
