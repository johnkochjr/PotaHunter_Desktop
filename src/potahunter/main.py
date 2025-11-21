"""
Main entry point for POTA Hunter application
"""

import sys
import logging


def main():
    """Initialize and run the application"""
    # Import only what we need for the splash screen first
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from potahunter.version import APP_NAME, APP_ORGANIZATION, APP_DOMAIN, APP_DISPLAY_NAME

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

    # Set macOS menu bar name
    if sys.platform == 'darwin':
        try:
            from Foundation import NSBundle
            bundle = NSBundle.mainBundle()
            if bundle:
                info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
                if info:
                    info['CFBundleName'] = APP_NAME
        except ImportError:
            # pyobjc-framework-Cocoa not installed, will show as "Python"
            pass

    # Set high DPI attributes before creating QApplication
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORGANIZATION)
    app.setOrganizationDomain(APP_DOMAIN)
    app.setApplicationDisplayName(APP_DISPLAY_NAME)

    # Show splash screen IMMEDIATELY before heavy imports
    from potahunter.ui.splash_screen import SplashScreen
    splash = SplashScreen()
    splash.show()
    app.processEvents()  # Ensure splash is shown immediately

    # NOW import the heavy modules while splash is showing
    from potahunter.ui.main_window import MainWindow

    # Update splash with final message
    splash.update_message("Initializing main window...")
    app.processEvents()

    # Create main window (this takes time)
    window = MainWindow()

    # Ready to go!
    splash.update_message("Ready! 73 de POTA Hunter...")
    app.processEvents()

    # Close splash and show main window
    splash.close_splash()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
