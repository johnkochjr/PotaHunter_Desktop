"""
Settings dialog for POTA Hunter application
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QHBoxLayout, QLabel, QTabWidget, QWidget, QCheckBox
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

        # XML API credentials (for callsign lookups)
        xml_header = QLabel("<b>XML API Credentials (for callsign lookups)</b>")
        qrz_layout.addWidget(xml_header)

        self.qrz_username = QLineEdit()
        self.qrz_username.setPlaceholderText("Your QRZ.com username")
        qrz_form.addRow("QRZ Username:", self.qrz_username)

        self.qrz_password = QLineEdit()
        self.qrz_password.setPlaceholderText("Your QRZ.com password")
        self.qrz_password.setEchoMode(QLineEdit.Password)
        qrz_form.addRow("QRZ Password:", self.qrz_password)

        qrz_layout.addSpacing(20)

        # Logbook API key (for log uploads)
        logbook_header = QLabel("<b>Logbook API Key (for log uploads)</b>")
        qrz_layout.addWidget(logbook_header)

        logbook_info = QLabel(
            "Enter your QRZ Logbook API key to enable log uploads.\n"
            "Get your API key from: https://logbook.qrz.com/api"
        )
        logbook_info.setWordWrap(True)
        logbook_info.setStyleSheet("font-style: italic; color: gray;")
        qrz_layout.addWidget(logbook_info)

        self.qrz_api_key = QLineEdit()
        self.qrz_api_key.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
        qrz_form.addRow("API Key:", self.qrz_api_key)

        qrz_layout.addLayout(qrz_form)

        # Auto-upload checkbox
        self.auto_upload_checkbox = QCheckBox("Automatically upload QSOs to QRZ Logbook when saving")
        self.auto_upload_checkbox.setEnabled(False)  # Disabled until API key is set
        qrz_layout.addWidget(self.auto_upload_checkbox)

        # Enable/disable auto-upload based on API key
        self.qrz_api_key.textChanged.connect(self._update_auto_upload_enabled)

        qrz_layout.addSpacing(10)

        auto_upload_note = QLabel(
            "Note: Auto-upload requires a valid API key. "
            "Enter your API key above to enable this option."
        )
        auto_upload_note.setWordWrap(True)
        auto_upload_note.setStyleSheet("font-style: italic; color: gray; font-size: 11px;")
        qrz_layout.addWidget(auto_upload_note)

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

        # Station Info Tab
        station_tab = QWidget()
        station_layout = QVBoxLayout(station_tab)

        station_info = QLabel(
            "Enter your station information. These values will be automatically "
            "included in your QSOs and ADIF exports."
        )
        station_info.setWordWrap(True)
        station_layout.addWidget(station_info)
        station_layout.addSpacing(10)

        station_form = QFormLayout()

        # Basic station info
        basic_header = QLabel("<b>Basic Information</b>")
        station_layout.addWidget(basic_header)

        self.my_callsign = QLineEdit()
        self.my_callsign.setPlaceholderText("Your callsign")
        station_form.addRow("Callsign:", self.my_callsign)

        self.operator = QLineEdit()
        self.operator.setPlaceholderText("Operator callsign (if different)")
        station_form.addRow("Operator:", self.operator)

        self.my_gridsquare_station = QLineEdit()
        self.my_gridsquare_station.setPlaceholderText("e.g., EN44av")
        station_form.addRow("Grid Square:", self.my_gridsquare_station)

        station_layout.addLayout(station_form)
        station_layout.addSpacing(15)

        # Location info
        location_header = QLabel("<b>Location</b>")
        station_layout.addWidget(location_header)

        location_form = QFormLayout()

        self.my_street = QLineEdit()
        self.my_street.setPlaceholderText("Street address")
        location_form.addRow("Street:", self.my_street)

        self.my_city = QLineEdit()
        self.my_city.setPlaceholderText("City")
        location_form.addRow("City:", self.my_city)

        self.my_county = QLineEdit()
        self.my_county.setPlaceholderText("e.g., Washington")
        location_form.addRow("County:", self.my_county)

        self.my_state = QLineEdit()
        self.my_state.setPlaceholderText("State/Province (2-letter code)")
        location_form.addRow("State:", self.my_state)

        self.my_postal_code = QLineEdit()
        self.my_postal_code.setPlaceholderText("ZIP/Postal code")
        location_form.addRow("Postal Code:", self.my_postal_code)

        self.my_country = QLineEdit()
        self.my_country.setPlaceholderText("e.g., United States")
        location_form.addRow("Country:", self.my_country)

        self.my_dxcc = QLineEdit()
        self.my_dxcc.setPlaceholderText("e.g., 291 for USA")
        location_form.addRow("DXCC:", self.my_dxcc)

        station_layout.addLayout(location_form)
        station_layout.addSpacing(15)

        # Coordinates
        coord_header = QLabel("<b>Coordinates</b>")
        station_layout.addWidget(coord_header)

        coord_form = QFormLayout()

        self.my_lat = QLineEdit()
        self.my_lat.setPlaceholderText("e.g., N044 52.635")
        coord_form.addRow("Latitude:", self.my_lat)

        self.my_lon = QLineEdit()
        self.my_lon.setPlaceholderText("e.g., W091 55.432")
        coord_form.addRow("Longitude:", self.my_lon)

        station_layout.addLayout(coord_form)
        station_layout.addSpacing(15)

        # Equipment
        equipment_header = QLabel("<b>Equipment</b>")
        station_layout.addWidget(equipment_header)

        equipment_form = QFormLayout()

        self.my_rig = QLineEdit()
        self.my_rig.setPlaceholderText("e.g., Yaesu FT-891")
        equipment_form.addRow("Radio:", self.my_rig)

        self.tx_pwr = QLineEdit()
        self.tx_pwr.setPlaceholderText("e.g., 100")
        equipment_form.addRow("TX Power (W):", self.tx_pwr)

        self.ant_az = QLineEdit()
        self.ant_az.setPlaceholderText("e.g., 90 (degrees)")
        equipment_form.addRow("Antenna Azimuth:", self.ant_az)

        station_layout.addLayout(equipment_form)

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

    def get_qrz_api_key(self):
        """
        Get QRZ Logbook API key from the dialog

        Returns:
            API key string
        """
        return self.qrz_api_key.text().strip()

    def set_qrz_api_key(self, api_key):
        """
        Set QRZ Logbook API key in the dialog

        Args:
            api_key: QRZ Logbook API key
        """
        self.qrz_api_key.setText(api_key)

    def get_auto_upload_enabled(self):
        """
        Get auto-upload setting

        Returns:
            True if auto-upload is enabled, False otherwise
        """
        return self.auto_upload_checkbox.isChecked()

    def set_auto_upload_enabled(self, enabled):
        """
        Set auto-upload setting

        Args:
            enabled: True to enable auto-upload, False to disable
        """
        self.auto_upload_checkbox.setChecked(enabled)

    def _update_auto_upload_enabled(self):
        """Enable/disable auto-upload checkbox based on API key presence"""
        has_api_key = len(self.qrz_api_key.text().strip()) > 0
        self.auto_upload_checkbox.setEnabled(has_api_key)
        if not has_api_key:
            self.auto_upload_checkbox.setChecked(False)

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

    # Station Info getters and setters
    def get_station_info(self):
        """Get all station information as dictionary"""
        return {
            'my_callsign': self.my_callsign.text().strip(),
            'operator': self.operator.text().strip(),
            'my_gridsquare': self.my_gridsquare_station.text().strip(),
            'my_street': self.my_street.text().strip(),
            'my_city': self.my_city.text().strip(),
            'my_county': self.my_county.text().strip(),
            'my_state': self.my_state.text().strip(),
            'my_postal_code': self.my_postal_code.text().strip(),
            'my_country': self.my_country.text().strip(),
            'my_dxcc': self.my_dxcc.text().strip(),
            'my_lat': self.my_lat.text().strip(),
            'my_lon': self.my_lon.text().strip(),
            'my_rig': self.my_rig.text().strip(),
            'tx_pwr': self.tx_pwr.text().strip(),
            'ant_az': self.ant_az.text().strip(),
        }

    def set_station_info(self, info):
        """Set station information from dictionary"""
        self.my_callsign.setText(info.get('my_callsign', ''))
        self.operator.setText(info.get('operator', ''))
        self.my_gridsquare_station.setText(info.get('my_gridsquare', ''))
        self.my_street.setText(info.get('my_street', ''))
        self.my_city.setText(info.get('my_city', ''))
        self.my_county.setText(info.get('my_county', ''))
        self.my_state.setText(info.get('my_state', ''))
        self.my_postal_code.setText(info.get('my_postal_code', ''))
        self.my_country.setText(info.get('my_country', ''))
        self.my_dxcc.setText(info.get('my_dxcc', ''))
        self.my_lat.setText(info.get('my_lat', ''))
        self.my_lon.setText(info.get('my_lon', ''))
        self.my_rig.setText(info.get('my_rig', ''))
        self.tx_pwr.setText(info.get('tx_pwr', ''))
        self.ant_az.setText(info.get('ant_az', ''))