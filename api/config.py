import json
import os
import secrets
import logging
from pathlib import Path
from utils.resource_manager import RM

logger = logging.getLogger(__name__)

class APIConfigManager:
    """
    Manages API server settings, including persistence and auto-generating secure API keys.
    """
    def __init__(self) -> None:
        self.config_path = RM.config() / "api_config.json"
        self.host = "0.0.0.0"
        self.port = 8000
        self.api_key = ""
        self.rate_limit_per_minute = 100
        self.enabled = True
        self.load_or_create()

    def load_or_create(self) -> None:
        """Loads configuration from JSON file or creates a default one if not found."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.host = data.get("host", "0.0.0.0")
                self.port = data.get("port", 8000)
                self.api_key = data.get("api_key", "")
                self.rate_limit_per_minute = data.get("rate_limit_per_minute", 100)
                self.enabled = data.get("enabled", True)
                
                # If API key is empty/missing, generate it
                if not self.api_key:
                    self.api_key = secrets.token_hex(32)
                    self.save()
                return
            except Exception as e:
                logger.error(f"Error loading API config: {e}. Re-creating default.")

        # Create new config
        self.api_key = secrets.token_hex(32)
        self.save()

    def save(self) -> None:
        """Saves current settings to api_config.json."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        data = {
            "host": self.host,
            "port": self.port,
            "api_key": self.api_key,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "enabled": self.enabled
        }
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            logger.info(f"API configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save API config: {e}")
