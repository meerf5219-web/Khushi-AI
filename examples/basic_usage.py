"""
examples/basic_usage.py
=======================
Demonstrates basic usage of Khushi AI's core cognitive brain
to process a text query offline.
"""

import sys
import os

# Append the parent directory to the path so python can find core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from brain.brain import Brain
    from brain.context import Context
    import logging

    # Configure minimal logging
    logging.basicConfig(level=logging.INFO)

    print("Initializing Khushi AI Brain subsystems...")
    # Instantiate the core brain
    brain = Brain()
    
    # Warm up semantic intelligence maps
    print("Warming up decision engines...")
    
    # Compose input text context
    query = "What is 15 percentage of 250?"
    print(f"\nUser query: '{query}'")
    
    # Run query through intent routing & response composer
    context = Context(raw_input=query)
    response = brain.process_pipeline(context)
    
    print("\n--- Response Compose Output ---")
    print(f"Reply: {response}")
    print("---------------------------------")
    
except ImportError as e:
    print(f"Error: Unable to import core modules. Make sure you run this from the project root. details: {e}")
except Exception as e:
    print(f"Failed to process query: {e}")
