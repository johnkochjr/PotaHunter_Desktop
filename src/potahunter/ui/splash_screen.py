"""
Splash screen with fun loading messages for POTA Hunter
"""

import random
from PySide6.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont

from potahunter.version import __version__, APP_DESCRIPTION


class SplashScreen(QSplashScreen):
    """Custom splash screen with rotating fun messages"""

    # Fun ham radio and POTA themed loading messages
    MESSAGES = [
        "Waking up the hamsters...",
        "Reaching out to the ionosphere...",
        "Phoning home in the stars...",
        "Tuning the antenna...",
        "Charging the flux capacitor...",
        "Calibrating the SWR meter...",
        "Warming up the tubes...",
        "Adjusting the linear amplifier...",
        "Checking for band openings...",
        "Scanning for DX...",
        "Hunting for rare parks...",
        "Loading the logbook...",
        "Contacting the mother ship...",
        "Bouncing signals off the moon...",
        "Summoning the band conditions...",
        "Preparing the QSL cards...",
        "Activating the transceiver...",
        "Connecting to the ether...",
        "Initializing the dipole...",
        "Starting the QRP rig...",
        "Powering up the final stage...",
        "Aligning the beam heading...",
        "Checking the propagation forecast...",
        "Loading park references...",
        "CQ CQ CQ, calling all stations...",
    ]

    def __init__(self):
        # Create a pixmap for the splash screen
        pixmap = QPixmap(500, 300)
        pixmap.fill(QColor(33, 37, 43))  # Dark background

        # Draw on the pixmap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Title
        title_font = QFont("Arial", 28, QFont.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(pixmap.rect().adjusted(20, 40, -20, -200),
                        Qt.AlignCenter, "POTA Hunter")

        # Subtitle
        subtitle_font = QFont("Arial", 12)
        painter.setFont(subtitle_font)
        painter.setPen(QColor(180, 180, 180))
        painter.drawText(pixmap.rect().adjusted(20, 100, -20, -160),
                        Qt.AlignCenter, APP_DESCRIPTION)

        # Version
        version_font = QFont("Arial", 10)
        painter.setFont(version_font)
        painter.setPen(QColor(140, 140, 140))
        painter.drawText(pixmap.rect().adjusted(20, 260, -20, -20),
                        Qt.AlignCenter, f"Version {__version__}")

        painter.end()

        super().__init__(pixmap, Qt.WindowStaysOnTopHint)

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        # Current message index
        self.message_index = 0

        # Set initial message
        self.show_message(self.MESSAGES[0])

        # Timer to cycle through messages
        self.timer = QTimer()
        self.timer.timeout.connect(self.cycle_message)
        self.timer.start(800)  # Change message every 800ms

    def cycle_message(self):
        """Cycle to the next fun message"""
        self.message_index = (self.message_index + 1) % len(self.MESSAGES)
        self.show_message(self.MESSAGES[self.message_index])

    def show_message(self, message):
        """Show a message on the splash screen"""
        self.showMessage(
            message,
            Qt.AlignBottom | Qt.AlignHCenter,
            QColor(100, 200, 255)  # Light blue color
        )

    def update_message(self, message):
        """
        Update the splash screen with a specific message (stops automatic cycling)

        Args:
            message: Custom message to display
        """
        self.timer.stop()  # Stop automatic cycling
        self.show_message(message)

    def close_splash(self):
        """Stop the timer and close the splash screen"""
        self.timer.stop()
        self.close()
