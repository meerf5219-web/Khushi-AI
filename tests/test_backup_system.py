import os
import io
import json
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from api.server import app, SimpleRateLimiter
from memory.backup import BackupManager
from utils.resource_manager import RM


@pytest.fixture
def temp_memory_setup(monkeypatch, tmp_path):
    """Mocks RM.memory and RM.data paths to keep test files sandbox-isolated."""
    mock_memory_dir = tmp_path / "memory"
    mock_data_dir = tmp_path / "data"
    mock_memory_dir.mkdir(parents=True, exist_ok=True)
    mock_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Write mock memory files
    with open(mock_memory_dir / "user_memory.json", "w", encoding="utf-8") as f:
        json.dump({"facts": {"name": "Faisal"}}, f)
    with open(mock_memory_dir / "world_model.json", "w", encoding="utf-8") as f:
        json.dump({"nodes": {"u1": {"label": "User"}}}, f)
        
    monkeypatch.setattr(RM, "memory", lambda: mock_memory_dir)
    monkeypatch.setattr(RM, "data", lambda relative="": mock_data_dir / relative if relative else mock_data_dir)
    
    return mock_memory_dir, mock_data_dir


def test_backup_create_list_restore(temp_memory_setup):
    """Verify creating a backup, checking lists, incorrect decrypts, and successful restores."""
    mem_dir, data_dir = temp_memory_setup
    
    bm = BackupManager()
    
    # 1. Create backup
    payload_path, meta_path = bm.create_backup("secure_pwd123", "Test version")
    assert payload_path.exists()
    assert meta_path.exists()
    
    # 2. List backups
    history = bm.list_backups()
    assert len(history) == 1
    assert history[0]["label"] == "Test version"
    
    # 3. Modify active memory files to simulate data loss / modification
    with open(mem_dir / "user_memory.json", "w") as f:
        json.dump({"facts": {"name": "Altered"}}, f)
        
    # 4. Decrypt with wrong password fails
    with pytest.raises(ValueError) as exc:
        bm.restore_backup(payload_path.name, "wrong_pwd")
    assert "Decryption failed" in str(exc.value)
    
    # Confirm active file is STILL the altered one (no restore took place)
    with open(mem_dir / "user_memory.json", "r") as f:
        assert json.load(f)["facts"]["name"] == "Altered"
        
    # 5. Decrypt with correct password succeeds
    success = bm.restore_backup(payload_path.name, "secure_pwd123")
    assert success is True
    
    # Confirm active file is restored to original "Faisal"
    with open(mem_dir / "user_memory.json", "r") as f:
        assert json.load(f)["facts"]["name"] == "Faisal"


def test_backup_import_export(temp_memory_setup):
    """Verify import and export helpers copy and rename backups correctly."""
    mem_dir, data_dir = temp_memory_setup
    bm = BackupManager()
    
    payload_path, meta_path = bm.create_backup("pwd123", "Export check")
    
    with open(payload_path, "rb") as f:
        enc_bytes = f.read()
    with open(meta_path, "r", encoding="utf-8") as f:
        meta_dict = json.load(f)
        
    # Import into sandbox
    new_name = bm.import_backup(enc_bytes, meta_dict)
    assert new_name != payload_path.stem
    assert (bm.backup_dir / f"{new_name}.enc").exists()
    assert (bm.backup_dir / f"{new_name}_meta.json").exists()


@pytest.fixture
def mock_brain():
    brain = MagicMock()
    return brain


@pytest.fixture
def client(mock_brain, temp_memory_setup):
    app.state.brain = mock_brain
    app.state.api_key = "test_backup_key"
    app.state.rate_limiter = SimpleRateLimiter(limit=100)
    with TestClient(app) as c:
        yield c


def test_api_backup_endpoints(client, temp_memory_setup):
    """Verify create, list, restore, export, and import REST routes."""
    # 1. Create Backup API
    r = client.post(
        "/backup/create",
        json={"password": "api_pwd_123", "label": "API version"},
        headers={"x-api-key": "test_backup_key"}
    )
    assert r.status_code == 200
    payload_file = r.json()["payload_file"]
    
    # 2. List Backups API
    r = client.get("/backup/list", headers={"x-api-key": "test_backup_key"})
    assert r.status_code == 200
    assert len(r.json()["backups"]) > 0
    
    # 3. Export Backup API
    r = client.get(f"/backup/export/{payload_file}", headers={"x-api-key": "test_backup_key"})
    assert r.status_code == 200
    assert len(r.content) > 0
    
    # 4. Restore Backup API
    r = client.post(
        "/backup/restore",
        json={"backup_name": payload_file, "password": "api_pwd_123"},
        headers={"x-api-key": "test_backup_key"}
    )
    assert r.status_code == 200
    
    # 5. Restore with invalid password returns 400
    r = client.post(
        "/backup/restore",
        json={"backup_name": payload_file, "password": "wrong_password"},
        headers={"x-api-key": "test_backup_key"}
    )
    assert r.status_code == 400
