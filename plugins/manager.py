import os
import logging
from typing import Dict, Any

from plugins.manifest import PluginManifest
from plugins.sandbox import RestrictedEnvironment
from plugins.sdk import PluginSDK

logger = logging.getLogger(__name__)

class PluginManager:
    """
    Discovers, loads, and unloads plugins dynamically.
    """
    def __init__(self, brain=None):
        self.brain = brain
        self.plugins_dir = os.path.join(os.path.dirname(__file__), "installed")
        self.active_plugins: Dict[str, Any] = {}
        self.manifests: Dict[str, PluginManifest] = {}
        
    def discover(self):
        """Scans the plugins/installed directory for manifests."""
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir, exist_ok=True)
            return
            
        for folder in os.listdir(self.plugins_dir):
            folder_path = os.path.join(self.plugins_dir, folder)
            if os.path.isdir(folder_path):
                manifest_path = os.path.join(folder_path, "manifest.json")
                if os.path.exists(manifest_path):
                    try:
                        manifest = PluginManifest(manifest_path)
                        self.manifests[manifest.id] = manifest
                    except Exception as e:
                        logger.error(f"Failed to load manifest in {folder}: {e}")

    def load_plugin(self, plugin_id: str) -> bool:
        """
        Hot loads a plugin into the restricted environment.
        """
        if plugin_id in self.active_plugins:
            logger.warning(f"Plugin {plugin_id} is already loaded.")
            return True
            
        manifest = self.manifests.get(plugin_id)
        if not manifest:
            logger.error(f"Plugin {plugin_id} not found in manifests.")
            return False
            
        if not manifest.validate_dependencies(self.active_plugins):
            return False
            
        entry_path = os.path.join(os.path.dirname(manifest.file_path), manifest.entrypoint)
        if not os.path.exists(entry_path):
            logger.error(f"Entrypoint {manifest.entrypoint} missing for {plugin_id}")
            return False
            
        try:
            with open(entry_path, 'r', encoding='utf-8') as f:
                code_str = f.read()
                
            # Create SDK and Sandbox
            sdk = PluginSDK(self.brain, manifest.permissions)
            sandbox = RestrictedEnvironment(manifest.permissions)
            
            # Execute
            module = sandbox.execute(code_str, sdk)
            
            # Call plugin initialization hook if present
            if hasattr(module, "on_load"):
                module.on_load()
                
            self.active_plugins[plugin_id] = module
            logger.info(f"Successfully loaded plugin: {plugin_id} v{manifest.version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_id}: {e}")
            return False

    def unload_plugin(self, plugin_id: str) -> bool:
        """
        Hot unloads a plugin.
        """
        if plugin_id not in self.active_plugins:
            return False
            
        try:
            module = self.active_plugins[plugin_id]
            if hasattr(module, "on_unload"):
                module.on_unload()
                
            del self.active_plugins[plugin_id]
            logger.info(f"Successfully unloaded plugin: {plugin_id}")
            return True
        except Exception as e:
            logger.error(f"Error unloading plugin {plugin_id}: {e}")
            return False
            
    def load_all(self):
        self.discover()
        for p_id in self.manifests.keys():
            self.load_plugin(p_id)
