"""
examples/memory_example.py
==========================
Demonstrates interaction with Khushi AI's persistent memory manager
and semantic context storage layers.
"""

import sys
import os

# Append the parent directory to the path so python can find core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from memory.manager import MemoryManager
    import logging

    logging.basicConfig(level=logging.INFO)
    
    print("Loading SQLite events database and profile maps...")
    memory_mgr = MemoryManager()
    
    # Write a new key-value pair to user memory profile
    print("\nAdding a new relationship preference...")
    memory_mgr.set_user_preference("theme", "glassmorphic-purple")
    
    # Retrieve details
    theme_pref = memory_mgr.get_user_preference("theme")
    print(f"Retrieved theme preference: '{theme_pref}'")
    
    # Commit changes to database
    print("Saving changes locally to user_memory.json...")
    memory_mgr.save_to_disk()
    print("Memory synchronized successfully.")

except ImportError as e:
    print(f"Error: Unable to import core modules. details: {e}")
except Exception as e:
    print(f"Error writing to memory module: {e}")
