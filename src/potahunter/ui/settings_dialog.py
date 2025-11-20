"""
Settings dialog for POTA Hunter application
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QHBoxLayout, QLabel, QTabWidget, QWidget, QCheckBox, QComboBox
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

        # CAT Control Tab
        cat_tab = QWidget()
        cat_layout = QVBoxLayout(cat_tab)

        cat_info = QLabel(
            "Configure CAT (Computer Aided Transceiver) control to sync frequency "
            "and mode with your radio."
        )
        cat_info.setWordWrap(True)
        cat_layout.addWidget(cat_info)
        cat_layout.addSpacing(10)

        cat_form = QFormLayout()

        # Radio model selection
        self.cat_radio_model = QComboBox()
        self.cat_radio_model.addItem("(None - Disabled)", "")
        # Import here to avoid circular dependencies
        from potahunter.services.cat_service import CATService
        for model in CATService.get_radio_models():
            self.cat_radio_model.addItem(model, model)
        cat_form.addRow("Radio Model:", self.cat_radio_model)

        # COM port selection
        self.cat_com_port = QComboBox()
        self.cat_com_port.setEditable(True)
        self.cat_com_port.addItem("(Select Port)", "")
        # Populate with available ports
        self._refresh_com_ports()
        cat_form.addRow("COM Port:", self.cat_com_port)

        # Refresh ports button
        refresh_ports_layout = QHBoxLayout()
        self.refresh_ports_button = QPushButton("Refresh Ports")
        self.refresh_ports_button.clicked.connect(self._refresh_com_ports)
        refresh_ports_layout.addWidget(self.refresh_ports_button)
        refresh_ports_layout.addStretch()
        cat_layout.addLayout(refresh_ports_layout)

        # Baud rate (dropdown with common values)
        baud_layout = QHBoxLayout()
        self.cat_baud_rate = QComboBox()
        self.cat_baud_rate.setEditable(True)
        self.cat_baud_rate.addItems([
            "Auto (radio default)",
            "4800",
            "9600",
            "19200",
            "38400",
            "57600",
            "115200"
        ])
        baud_layout.addWidget(self.cat_baud_rate)

        self.detect_baud_button = QPushButton("Auto-Detect")
        self.detect_baud_button.clicked.connect(self.detect_baud_rate)
        baud_layout.addWidget(self.detect_baud_button)

        cat_form.addRow("Baud Rate:", baud_layout)

        cat_layout.addLayout(cat_form)
        cat_layout.addSpacing(15)

        # Power Levels Section
        power_header = QLabel("<b>Power Levels by Mode</b>")
        cat_layout.addWidget(power_header)

        power_info = QLabel(
            "Set transmit power levels (in watts) for different mode categories.\n"
            "Leave blank to use radio's current power setting."
        )
        power_info.setWordWrap(True)
        power_info.setStyleSheet("font-style: italic; color: gray; font-size: 11px;")
        cat_layout.addWidget(power_info)

        power_form = QFormLayout()

        self.cat_power_ssb = QLineEdit()
        self.cat_power_ssb.setPlaceholderText("e.g., 100")
        self.cat_power_ssb.setMaximumWidth(150)
        power_form.addRow("SSB Power (Watts):", self.cat_power_ssb)

        self.cat_power_data = QLineEdit()
        self.cat_power_data.setPlaceholderText("e.g., 50")
        self.cat_power_data.setMaximumWidth(150)
        power_form.addRow("Data Power (Watts):", self.cat_power_data)

        self.cat_power_cw = QLineEdit()
        self.cat_power_cw.setPlaceholderText("e.g., 100")
        self.cat_power_cw.setMaximumWidth(150)
        power_form.addRow("CW Power (Watts):", self.cat_power_cw)

        cat_layout.addLayout(power_form)

        power_note = QLabel(
            "<b>Mode Categories:</b><br>"
            "• <b>SSB:</b> USB, LSB, FM, AM (phone modes)<br>"
            "• <b>Data:</b> FT8, FT4, RTTY, PSK31, and other digital modes<br>"
            "• <b>CW:</b> All CW modes"
        )
        power_note.setWordWrap(True)
        power_note.setStyleSheet("font-size: 11px; color: gray;")
        cat_layout.addWidget(power_note)

        cat_layout.addSpacing(10)

        # Enable CAT control checkbox
        self.cat_enabled = QCheckBox("Enable CAT control")
        cat_layout.addWidget(self.cat_enabled)

        cat_layout.addSpacing(10)

        # Test connection button
        test_cat_layout = QHBoxLayout()
        self.test_cat_button = QPushButton("Test Connection")
        self.test_cat_button.clicked.connect(self.test_cat_connection)
        test_cat_layout.addWidget(self.test_cat_button)
        test_cat_layout.addStretch()
        cat_layout.addLayout(test_cat_layout)

        # Status label for test results
        self.cat_test_result = QLabel("")
        self.cat_test_result.setWordWrap(True)
        cat_layout.addWidget(self.cat_test_result)

        cat_layout.addSpacing(10)

        # Information about CAT control
        cat_help = QLabel(
            "<b>Notes:</b><br>"
            "• Ensure your radio's CAT/USB interface is properly configured<br>"
            "• Most modern radios use USB virtual COM ports<br>"
            "• Baud rate is usually set automatically based on radio model<br>"
            "• You may need to install USB drivers for your radio"
        )
        cat_help.setWordWrap(True)
        cat_help.setStyleSheet("font-size: 11px; color: gray;")
        cat_layout.addWidget(cat_help)

        cat_layout.addStretch()
        tabs.addTab(cat_tab, "CAT Control")

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

    # CAT Control methods
    def _refresh_com_ports(self):
        """Refresh the list of available COM ports"""
        from potahunter.services.cat_service import CATService

        current_port = self.cat_com_port.currentText()
        self.cat_com_port.clear()
        self.cat_com_port.addItem("(Select Port)", "")

        ports = CATService.get_available_ports()
        for port in ports:
            self.cat_com_port.addItem(port, port)

        # Restore previous selection if it still exists
        index = self.cat_com_port.findText(current_port)
        if index >= 0:
            self.cat_com_port.setCurrentIndex(index)

    def detect_baud_rate(self):
        """Auto-detect the correct baud rate for the selected radio"""
        from potahunter.services.cat_service import CATService

        radio_model = self.cat_radio_model.currentData()
        com_port = self.cat_com_port.currentText()

        if not radio_model:
            self.cat_test_result.setText(
                "<span style='color: orange;'>⚠️ Please select a radio model first</span>"
            )
            return

        if not com_port or com_port == "(Select Port)":
            self.cat_test_result.setText(
                "<span style='color: orange;'>⚠️ Please select a COM port first</span>"
            )
            return

        self.cat_test_result.setText("<i>Auto-detecting baud rate...</i>")
        self.detect_baud_button.setEnabled(False)
        self.test_cat_button.setEnabled(False)

        # Run detection
        detected_baud = CATService.detect_baud_rate(com_port, radio_model)

        if detected_baud:
            # Set the detected baud rate in the combo box
            self.cat_baud_rate.setCurrentText(str(detected_baud))
            self.cat_test_result.setText(
                f"<span style='color: green;'>✓ Detected baud rate: {detected_baud}</span>"
            )
        else:
            self.cat_test_result.setText(
                "<span style='color: orange;'>⚠️ Could not auto-detect baud rate. "
                "Try entering it manually or check radio connection.</span>"
            )

        self.detect_baud_button.setEnabled(True)
        self.test_cat_button.setEnabled(True)

    def test_cat_connection(self):
        """Test CAT connection to radio"""
        from potahunter.services.cat_service import CATService

        radio_model = self.cat_radio_model.currentData()
        com_port = self.cat_com_port.currentText()
        baud_rate_str = self.cat_baud_rate.currentText().strip()

        if not radio_model:
            self.cat_test_result.setText(
                "<span style='color: orange;'>⚠️ Please select a radio model</span>"
            )
            return

        if not com_port or com_port == "(Select Port)":
            self.cat_test_result.setText(
                "<span style='color: orange;'>⚠️ Please select a COM port</span>"
            )
            return

        self.cat_test_result.setText("<i>Testing connection...</i>")
        self.test_cat_button.setEnabled(False)

        # Parse custom baud rate if provided (skip "Auto" option)
        custom_baud = None
        if baud_rate_str and not baud_rate_str.startswith("Auto"):
            try:
                custom_baud = int(baud_rate_str)
            except ValueError:
                self.cat_test_result.setText(
                    "<span style='color: red;'>✗ Invalid baud rate</span>"
                )
                self.test_cat_button.setEnabled(True)
                return

        # Test connection
        cat = CATService()

        # Try to connect
        try:
            if cat.connect(com_port, radio_model, custom_baud):
                freq = cat.get_frequency()
                mode = cat.get_mode()
                cat.disconnect()

                freq_mhz = freq / 1_000_000 if freq else 0
                self.cat_test_result.setText(
                    f"<span style='color: green;'>✓ Connection successful!<br>"
                    f"Frequency: {freq_mhz:.6f} MHz<br>"
                    f"Mode: {mode}</span>"
                )
            else:
                # Connection failed - provide more details
                radio_config = CATService.RADIO_MODELS.get(radio_model, {})
                protocol = radio_config.get('protocol', 'unknown')
                baud = custom_baud if custom_baud else radio_config.get('baud', 'unknown')

                self.cat_test_result.setText(
                    f"<span style='color: red;'>✗ Connection failed<br>"
                    f"Protocol: {protocol}<br>"
                    f"Baud rate: {baud}<br><br>"
                    f"Possible issues:<br>"
                    f"• Radio not responding to commands<br>"
                    f"• Wrong baud rate (check radio settings)<br>"
                    f"• CAT interface disabled in radio menu<br>"
                    f"• Wrong radio model selected</span>"
                )
        except Exception as e:
            self.cat_test_result.setText(
                f"<span style='color: red;'>✗ Error: {str(e)}</span>"
            )

        self.test_cat_button.setEnabled(True)

    def get_cat_settings(self):
        """Get CAT control settings as dictionary"""
        baud_str = self.cat_baud_rate.currentText().strip()
        # Parse baud rate, ignoring "Auto" option
        baud_rate = None
        if baud_str and not baud_str.startswith("Auto"):
            try:
                baud_rate = int(baud_str)
            except ValueError:
                baud_rate = None

        # Parse power levels
        power_ssb = None
        power_data = None
        power_cw = None

        try:
            ssb_text = self.cat_power_ssb.text().strip()
            if ssb_text:
                power_ssb = int(ssb_text)
        except ValueError:
            pass

        try:
            data_text = self.cat_power_data.text().strip()
            if data_text:
                power_data = int(data_text)
        except ValueError:
            pass

        try:
            cw_text = self.cat_power_cw.text().strip()
            if cw_text:
                power_cw = int(cw_text)
        except ValueError:
            pass

        return {
            'cat_enabled': self.cat_enabled.isChecked(),
            'cat_radio_model': self.cat_radio_model.currentData(),
            'cat_com_port': self.cat_com_port.currentText(),
            'cat_baud_rate': baud_rate,
            'cat_power_ssb': power_ssb,
            'cat_power_data': power_data,
            'cat_power_cw': power_cw,
        }

    def set_cat_settings(self, settings):
        """Set CAT control settings from dictionary"""
        self.cat_enabled.setChecked(settings.get('cat_enabled', False))

        # Set radio model
        radio_model = settings.get('cat_radio_model', '')
        index = self.cat_radio_model.findData(radio_model)
        if index >= 0:
            self.cat_radio_model.setCurrentIndex(index)

        # Set COM port
        com_port = settings.get('cat_com_port', '')
        if com_port:
            index = self.cat_com_port.findText(com_port)
            if index >= 0:
                self.cat_com_port.setCurrentIndex(index)
            else:
                self.cat_com_port.setEditText(com_port)

        # Set baud rate
        baud_rate = settings.get('cat_baud_rate')
        if baud_rate:
            # Try to find the baud rate in the combo box
            index = self.cat_baud_rate.findText(str(baud_rate))
            if index >= 0:
                self.cat_baud_rate.setCurrentIndex(index)
            else:
                # If not found, set it as custom text
                self.cat_baud_rate.setCurrentText(str(baud_rate))
        else:
            # Default to "Auto"
            self.cat_baud_rate.setCurrentIndex(0)

        # Set power levels
        power_ssb = settings.get('cat_power_ssb')
        if power_ssb is not None:
            self.cat_power_ssb.setText(str(power_ssb))

        power_data = settings.get('cat_power_data')
        if power_data is not None:
            self.cat_power_data.setText(str(power_data))

        power_cw = settings.get('cat_power_cw')
        if power_cw is not None:
            self.cat_power_cw.setText(str(power_cw))