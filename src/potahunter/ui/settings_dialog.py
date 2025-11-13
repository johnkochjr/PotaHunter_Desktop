"""
Settings dialog for POTA Hunter application
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QHBoxLayout, QLabel, QTabWidget, QWidget
)
from PySide6.QtCore import Qt


class SettingsDialog(QDialog):
    """Settings dialog for application configuration"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Create tab widget
        tabs = QTabWidget()

        # QRZ Settings Tab
        qrz_tab = QWidget()
        qrz_layout = QVBoxLayout(qrz_tab)

        # QRZ credentials section
        qrz_form = QFormLayout()

        info_label = QLabel(
            "Enter your QRZ.com credentials to enable real-time callsign lookups.\n"
            "Requires an active QRZ XML subscription."
        )
        info_label.setWordWrap(True)
        qrz_layout.addWidget(info_label)
        qrz_layout.addSpacing(10)

        self.qrz_username = QLineEdit()
        self.qrz_username.setPlaceholderText("Your QRZ.com username")
        qrz_form.addRow("QRZ Username:", self.qrz_username)

        self.qrz_password = QLineEdit()
        self.qrz_password.setPlaceholderText("Your QRZ.com password")
        self.qrz_password.setEchoMode(QLineEdit.Password)
        qrz_form.addRow("QRZ Password:", self.qrz_password)

        qrz_layout.addLayout(qrz_form)

        # Add test button
        test_button_layout = QHBoxLayout()
        self.test_qrz_button = QPushButton("Test Credentials")
        self.test_qrz_button.clicked.connect(self.test_qrz_credentials)
        test_button_layout.addWidget(self.test_qrz_button)
        test_button_layout.addStretch()

        qrz_layout.addLayout(test_button_layout)

        # Status label for test results
        self.qrz_test_result = QLabel("")
        self.qrz_test_result.setWordWrap(True)
        qrz_layout.addWidget(self.qrz_test_result)

        qrz_layout.addStretch()

        tabs.addTab(qrz_tab, "QRZ Credentials")

        # Station Info Tab (for future use)
        station_tab = QWidget()
        station_layout = QVBoxLayout(station_tab)
        station_layout.addWidget(QLabel("Station settings coming soon..."))
        station_layout.addStretch()
        tabs.addTab(station_tab, "Station Info")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        self.save_button.setDefault(True)
        button_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def get_qrz_credentials(self):
        """
        Get QRZ credentials from the dialog

        Returns:
            Tuple of (username, password)
        """
        return (
            self.qrz_username.text().strip(),
            self.qrz_password.text().strip()
        )

    def set_qrz_credentials(self, username, password):
        """
        Set QRZ credentials in the dialog

        Args:
            username: QRZ username
            password: QRZ password
        """
        self.qrz_username.setText(username)
        self.qrz_password.setText(password)
    def test_qrz_credentials(self):
        """Test QRZ credentials by attempting authentication"""
        from potahunter.services.qrz_api import QRZAPIService
        
        username = self.qrz_username.text().strip()
        password = self.qrz_password.text().strip()
        
        if not username or not password:
            self.qrz_test_result.setText(
                "<span style='color: orange;'>⚠️ Please enter both username and password</span>"
            )
            return
        
        self.qrz_test_result.setText("<i>Testing credentials...</i>")
        self.test_qrz_button.setEnabled(False)
        
        # Test authentication
        qrz = QRZAPIService()
        qrz.set_credentials(username, password)
        
        if qrz.authenticate():
            self.qrz_test_result.setText(
                "<span style='color: green;'>✓ Credentials valid! Authentication successful.</span>"
            )
        else:
            self.qrz_test_result.setText(
                "<span style='color: red;'>✗ Authentication failed. "
                "Check your username, password, and QRZ subscription status.</span>"
            )
        
        self.test_qrz_button.setEnabled(True)