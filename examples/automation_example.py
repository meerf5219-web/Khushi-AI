"""
examples/automation_example.py
==============================
Demonstrates safe system automation API usage including
keyboard writing and volume adjustment triggers.
"""

import sys
import os

# Append the parent directory to the path so python can find core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from automation.keyboard import KeyboardController
    from automation.mouse import MouseController
    from skills.volume_skill import VolumeSkill
    
    print("Initializing keyboard controller...")
    keyboard = KeyboardController()
    
    print("Initializing mouse controller...")
    mouse = MouseController()
    
    print("\nSimulation: Safe Desktop Automation Operations:")
    # Get current cursor position (safe read query)
    pos = mouse.get_position()
    print(f"Current cursor coordinates: X={pos[0]}, Y={pos[1]}")
    
    # Adjust speaker volume using skill adapter (runs safely on Windows endpoints)
    print("\nInitializing Volume Skill interface...")
    vol_skill = VolumeSkill()
    print("Muting system volume...")
    vol_skill.set_mute(True)
    print("Unmuting system volume...")
    vol_skill.set_mute(False)
    print("\nAutomation sequence complete.")

except ImportError as e:
    print(f"Error: Unable to import core modules. details: {e}")
except Exception as e:
    print(f"Automation execution failed: {e}")
