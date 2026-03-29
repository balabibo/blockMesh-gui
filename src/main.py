#!/usr/bin/env python3
"""
blockMesh-gui - Main Entry Point
OpenFOAM blockMeshDict GUI Generator
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


def main():
    """Application entry point"""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Import and show main window
    from src.gui.main_window import MainWindow
    
    app = QApplication(sys.argv)
    app.setApplicationName("blockMesh-gui")
    app.setApplicationVersion("0.1.0")
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
