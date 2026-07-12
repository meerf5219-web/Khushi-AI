import pytest
import os
import json
from unittest.mock import MagicMock
from plugins.manager import PluginManager
from plugins.sandbox import RestrictedEnvironment
from plugins.sdk import PluginSDK

def test_sandbox_blocks_dangerous_builtins():
    """Verify that the RestrictedEnvironment removes `eval` and `exec`."""
    sandbox = RestrictedEnvironment(permissions=[])
    
    code = "result = eval('1 + 1')"
    
    with pytest.raises(NameError) as exc:
        sandbox.execute(code, sdk_instance=None)
        
    assert "name 'eval' is not defined" in str(exc.value)

def test_sandbox_blocks_os_import():
    """Verify that importing `os` throws an error without SYSTEM_ACCESS."""
    sandbox = RestrictedEnvironment(permissions=[])
    
    code = "import os\nos.system('echo hacked')"
    
    with pytest.raises(ImportError) as exc:
        sandbox.execute(code, sdk_instance=None)
        
    assert "restricted by sandbox policies" in str(exc.value)

def test_sandbox_allows_system_access_if_permitted():
    """Verify that SYSTEM_ACCESS permission allows os module."""
    sandbox = RestrictedEnvironment(permissions=["SYSTEM_ACCESS"])
    
    code = "import os\nresult = os.name"
    
    module = sandbox.execute(code, sdk_instance=None)
    assert hasattr(module, 'result')

def test_plugin_sdk_memory_proxy():
    brain = MagicMock()
    brain.memory.get_memory.return_value = "secret"
    
    # Missing permission
    sdk_no_perms = PluginSDK(brain, permissions=[])
    with pytest.raises(PermissionError):
        sdk_no_perms.memory.read("key")
        
    # Valid permission
    sdk_valid = PluginSDK(brain, permissions=["READ_MEMORY"])
    assert sdk_valid.memory.read("key") == "secret"

@pytest.fixture
def mock_plugin_dir(tmp_path):
    installed = tmp_path / "installed"
    installed.mkdir()
    
    test_plugin = installed / "test_plugin"
    test_plugin.mkdir()
    
    manifest = {
        "id": "test_plugin",
        "version": "1.0",
        "permissions": ["READ_MEMORY"],
        "entrypoint": "main.py"
    }
    
    with open(test_plugin / "manifest.json", "w") as f:
        json.dump(manifest, f)
        
    with open(test_plugin / "main.py", "w") as f:
        f.write("def on_load():\n    sdk.log('Plugin initialized!')\n")
        
    return str(tmp_path)

def test_plugin_manager_loads_plugin(mock_plugin_dir):
    manager = PluginManager(brain=MagicMock())
    manager.plugins_dir = os.path.join(mock_plugin_dir, "installed")
    
    manager.discover()
    assert "test_plugin" in manager.manifests
    
    success = manager.load_plugin("test_plugin")
    assert success is True
    assert "test_plugin" in manager.active_plugins
    
    manager.unload_plugin("test_plugin")
    assert "test_plugin" not in manager.active_plugins
