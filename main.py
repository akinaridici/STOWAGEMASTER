"""Main entry point for Tanker Stowage Plan application"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from ui.main_window import MainWindow


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Tanker Stowage Plan")
    app.setOrganizationName("Stowage Master")
    
    # Set application icon
    icon_path = Path(__file__).parent / "storage_manager.ico"
    if not icon_path.exists():
        # Fallback to stowmanager.ico if storage_manager.ico doesn't exist
        icon_path = Path(__file__).parent / "stowmanager.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

