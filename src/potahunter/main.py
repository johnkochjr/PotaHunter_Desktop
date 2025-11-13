"""
Main entry point for POTA Hunter application
"""

import sys
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from potahunter.ui.main_window import MainWindow


def set_macos_app_name():
    """Set the application name for macOS menu bar"""
    if sys.platform == 'darwin':
        try:
            from Foundation import NSBundle
            bundle = NSBundle.mainBundle()
            if bundle:
                info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
                if info:
                    info['CFBundleName'] = 'POTA Hunter'
        except ImportError:
            # pyobjc-framework-Cocoa not installed, will show as "Python"
            pass


def main():
    """Initialize and run the application"""
    # Configure logging FIRST (before any other imports that might log)
    logging.basicConfig(
        level=logging.DEBUG,  # Use DEBUG to see everything
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('potahunter.log'),  # Logs to file
            logging.StreamHandler()  # Also prints to console
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Starting POTA Hunter application")
    logger.info("=" * 60)

    # Set macOS menu bar name
    set_macos_app_name()

    # Set high DPI attributes before creating QApplication
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("POTA Hunter")
    app.setOrganizationName("POTA Hunter")
    app.setOrganizationDomain("potahunter.app")
    app.setApplicationDisplayName("POTA Hunter")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
