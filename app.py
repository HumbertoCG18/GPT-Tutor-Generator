#!/usr/bin/env python3
"""
Academic Tutor Repo Builder V3

This file is now a thin bootstrap wrapper around the decoupled `src/` modular architecture.
To run the application, you can execute this file directly, or use:
python -m src
"""

import sys

try:
    from src.__main__ import main
except ImportError as e:
    print(f"Error loading the application modules: {e}")
    print("Please ensure you are running this from the repository root.")
    sys.exit(1)

if __name__ == "__main__":
    main()
