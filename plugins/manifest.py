import json
import logging
import os
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class PluginManifest:
    """
    Parses and validates a plugin's manifest.json.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data: Dict = {}
        
        self.id = ""
        self.version = ""
        self.permissions = []
        self.entrypoint = "main.py"
        self.dependencies = []
        
        self._load()
        
    def _load(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Manifest not found: {self.file_path}")
            
        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
            
        self.id = self.data.get("id", "unknown_plugin")
        self.version = self.data.get("version", "1.0.0")
        self.permissions = self.data.get("permissions", [])
        self.entrypoint = self.data.get("entrypoint", "main.py")
        self.dependencies = self.data.get("requires", [])
        
    def validate_dependencies(self, installed_plugins: dict) -> bool:
        """
        Checks if the required plugins are present and loaded.
        """
        for req in self.dependencies:
            # req format: "other_plugin_id>=1.0" or just "other_plugin_id"
            # For simplicity, we just check existence by ID
            req_id = req.split(">")[0].split("=")[0].strip()
            if req_id not in installed_plugins:
                logger.error(f"Plugin '{self.id}' is missing dependency '{req_id}'.")
                return False
        return True
