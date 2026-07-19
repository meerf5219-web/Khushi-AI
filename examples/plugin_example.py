"""
examples/plugin_example.py
==========================
Demonstrates how to structure, load, and execute a custom plugin
using the sandboxed plugin manager SDK.
"""

import sys
import os
import json

# Append the parent directory to the path so python can find core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from plugins.manager import PluginManager
    from plugins.manifest import PluginManifest
    
    # Define a simple plugin manifest in JSON format
    manifest_data = {
        "name": "QuickLoggerPlugin",
        "version": "1.0.0",
        "description": "Log runtime actions to external file.",
        "author": "Open Source Contributor",
        "entry_point": "plugin.py",
        "permissions": ["filesystem_write", "read_env"]
    }
    
    print("Parsing manifest details...")
    manifest = PluginManifest.from_dict(manifest_data)
    print(f"Plugin name: {manifest.name} (v{manifest.version})")
    
    print("\nInitializing Plugin sandbox manager...")
    manager = PluginManager()
    
    # Load manifest into registry
    manager.register_manifest(manifest)
    print("Plugin registered successfully into sandbox system.")

except ImportError as e:
    print(f"Error: Unable to import core modules. details: {e}")
except Exception as e:
    print(f"Error initializing plugin mockup: {e}")
