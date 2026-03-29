#!/usr/bin/env python3
"""
Run blockMesh-gui GUI
Use this script to launch the application from project root
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.gui.main_window import main

if __name__ == "__main__":
    main()
