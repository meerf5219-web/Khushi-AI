import asyncio
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
    def mock_think(text):
        event_bus.publish("STREAM_TOKEN", {"token": "Hi", "full_text": "Hi"})
        event_bus.publish("STREAM_TOKEN", {"token": " Faisal", "full_text": "Hi Faisal"})
        return "Hello Faisal."
    brain.think.side_effect = mock_think
    brain.memory.recall.return_value = "blue"
    
    # Mock companion engine and store
    brain.cie = MagicMock()
    brain.cie._store = MagicMock()
    brain.cie._store.get_summary.return_value = {
        "identity": {"records": {}},
        "goals": {"records": {"g1": {"payload": {"value": "crack upsc", "id": "g1"}}}},
        "projects": {"records": {"p1": {"payload": {"value": "khushi", "id": "p1"}}}},
        "timeline": {"records": []}
    }
    
    # Mock plugin manager
    plugin_mgr = MagicMock()
    plugin_mgr.active_plugins = {"test_plugin": MagicMock()}
    manifest = MagicMock()
    manifest.id = "test_plugin"
    manifest.version = "1.0"
    manifest.permissions = []
    manifest.entrypoint = "main.py"
    plugin_mgr.manifests = {"test_plugin": manifest}
    plugin_mgr.load_plugin.return_value = True
    plugin_mgr.unload_plugin.return_value = True
    brain.plugin_manager = plugin_mgr

    # Mock agentic engine
    agentic_engine = MagicMock()
    agentic_engine.goal_manager.get_goals.return_value = [{"id": "g1", "name": "crack upsc"}]
    agentic_engine.process.return_value = "Goal created"
    brain.conversation_pipeline = MagicMock()
    brain.conversation_pipeline.agentic_engine = agentic_engine
    
    return brain


@pytest.fixture
def client(mock_brain):
    app.state.brain = mock_brain
    app.state.api_key = "test_secret_key"
    app.state.rate_limiter = SimpleRateLimiter(limit=50) # High limit to avoid throttling test requests
    with TestClient(app) as c:
        yield c


def test_unauthenticated_request(client):
    """Verify that endpoints require auth and return 401 when missing."""
    r = client.post("/chat", json={"message": "hello"})
    assert r.status_code == 401


def test_authenticated_chat(client):
    """Verify that chat endpoint succeeds with valid API key."""
    # Custom header authentication
    r = client.post(
        "/chat",
        json={"message": "hello"},
        headers={"x-api-key": "test_secret_key"}
    )
    assert r.status_code == 200
    assert r.json() == {"response": "Hello Faisal."}

    # Query token authentication
    r = client.post(
        "/chat?token=test_secret_key",
        json={"message": "hello"}
    )
    assert r.status_code == 200

    # Bearer token authentication
    r = client.post(
        "/chat",
        json={"message": "hello"},
        headers={"Authorization": "Bearer test_secret_key"}
    )
    assert r.status_code == 200


def test_memory_endpoints(client):
    """Verify GET, POST, and key-specific memory lookups."""
    # GET /memory
    r = client.get("/memory", headers={"x-api-key": "test_secret_key"})
    assert r.status_code == 200
    assert "legacy" in r.json()
    assert "companion" in r.json()

    # GET /memory/{key}
    r = client.get("/memory/colour", headers={"x-api-key": "test_secret_key"})
    assert r.status_code == 200
    assert r.json() == {"key": "colour", "value": "blue"}

    # POST /memory
    r = client.post(
        "/memory",
        json={"key": "colour", "value": "red", "category": "preferences"},
        headers={"x-api-key": "test_secret_key"}
    )
    assert r.status_code == 200
    assert r.json() == {"status": "success", "message": "Saved memory 'colour'"}


def test_goals_and_projects(client):
    """Verify Goals and Projects APIs."""
    # GET /goals
    r = client.get("/goals", headers={"x-api-key": "test_secret_key"})
    assert r.status_code == 200
    
    # POST /goals
    r = client.post(
        "/goals",
        json={"text": "my goal is to crack UPSC"},
        headers={"x-api-key": "test_secret_key"}
    )
    assert r.status_code == 200
    assert r.json() == {"status": "success", "result": "Goal created"}

    # GET /projects
    r = client.get("/projects", headers={"x-api-key": "test_secret_key"})
    assert r.status_code == 200
    assert "projects" in r.json()

    # POST /projects
    r = client.post(
        "/projects",
        json={"name": "Build Khushi API", "description": "Expose APIs"},
        headers={"x-api-key": "test_secret_key"}
    )
    assert r.status_code == 200
    assert r.json()["status"] == "success"


def test_automation_endpoints(client):
    """Verify /automation GET and POST status/trigger endpoints."""
    # GET /automation
    r = client.get("/automation", headers={"x-api-key": "test_secret_key"})
    assert r.status_code == 200
    assert "active_workers" in r.json()

    # POST /automation (trigger mock calculator)
    r = client.post(
        "/automation",
        json={"action": "open_calculator"},
        headers={"x-api-key": "test_secret_key"}
    )
    assert r.status_code == 200
    assert "action_id" in r.json()


def test_plugins_and_status(client):
    """Verify plugins management and unauthenticated system status."""
    # GET /plugins
    r = client.get("/plugins", headers={"x-api-key": "test_secret_key"})
    assert r.status_code == 200
    assert "active_plugins" in r.json()

    # POST /plugins load
    r = client.post(
        "/plugins",
        json={"id": "test_plugin", "action": "load"},
        headers={"x-api-key": "test_secret_key"}
    )
    assert r.status_code == 200

    # GET /status (Public)
    r = client.get("/status")
    assert r.status_code == 200
    assert r.json()["status"] == "online"


def test_rate_limiting(mock_brain):
    """Verify rate-limiter middleware throttles excess requests."""
    app.state.brain = mock_brain
    app.state.api_key = "test_secret_key"
    app.state.rate_limiter = SimpleRateLimiter(limit=2, window_seconds=5)

    with TestClient(app) as local_client:
        r = local_client.get("/status")
        assert r.status_code == 200

        r = local_client.get("/status")
        assert r.status_code == 200

        r = local_client.get("/status")
        assert r.status_code == 429


def test_websocket_chat(client):
    """Verify WebSocket connection, auth, and streaming tokens/responses."""
    # Attempt connection with bad key
    with pytest.raises(Exception):
        with client.websocket_connect("/chat?token=bad_key"):
            pass

    # Connection with valid key
    with client.websocket_connect("/chat?token=test_secret_key") as ws:
        ws.send_text("hello")

        # Receive streamed tokens
        t1 = ws.receive_json()
        assert t1 == {"event": "token", "token": "Hi"}

        t2 = ws.receive_json()
        assert t2 == {"event": "token", "token": " Faisal"}

        # Receive final response
        resp = ws.receive_json()
        assert resp["event"] == "response"
        assert resp["response"] == "Hello Faisal."

        # Receive done event
        done = ws.receive_json()
        assert done == {"event": "done"}
