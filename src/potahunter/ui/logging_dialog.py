"""
Logging dialog for entering QSO details
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QMessageBox,
    QComboBox, QTextEdit
)
from PySide6.QtCore import Qt, QSettings
from datetime import datetime

from potahunter.models.qso import QSO
from potahunter.models.database import DatabaseManager


def resolve_mode_for_radio(mode: str, frequency_mhz: float) -> str:
    """
    Resolve mode strings to radio-appropriate modes based on frequency

    Args:
        mode: The mode string (e.g., 'SSB', 'CW', 'FT8', 'FT4', 'PSK31')
        frequency_mhz: Frequency in MHz

    Returns:
        Resolved mode appropriate for CAT control

    Conversions:
    - 'SSB' → 'USB' or 'LSB' based on frequency
    - 'CW' → 'CW-U' or 'CW-L' based on frequency
    - 'FT8', 'FT4', 'PSK31', 'RTTY' → 'DATA-U' or 'DATA-L' based on frequency
    - Other modes returned unchanged

    Amateur radio convention:
    - Below 10 MHz: Lower sideband (LSB, CW-L, DATA-L)
    - 10 MHz and above: Upper sideband (USB, CW-U, DATA-U)
    """
    mode_upper = mode.upper()

    # Digital modes that should be converted to DATA-U or DATA-L
    digital_modes = {'FT8', 'FT4', 'PSK31', 'PSK', 'RTTY', 'JS8', 'JS8CALL', 'CW'}

    if mode_upper == "SSB":
        # SSB voice mode
        return "LSB" if frequency_mhz < 10.0 else "USB"
    elif mode_upper == "CW":
        # CW mode
        return "CW-L" if frequency_mhz < 10.0 else "CW-U"
    elif mode_upper in digital_modes:
        # Digital modes use DATA-L or DATA-U
        return "DATA-L" if frequency_mhz < 10.0 else "DATA-U"

    return mode


class LoggingDialog(QDialog):
    """Dialog for logging a QSO with prefilled spot data"""

    # Common amateur radio modes
    MODES = ["SSB", "USB", "LSB", "CW", "FM", "AM", "RTTY", "PSK31", "FT8", "FT4", "JS8"]

    def __init__(self, spot_data: dict, parent=None, cat_service=None):
        super().__init__(parent)
        self.spot_data = spot_data
        self.db_manager = DatabaseManager()
        self.settings = QSettings()
        self.cat_service = cat_service
        self.init_ui()
        self.prefill_data()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Log QSO")
        self.setModal(True)
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Log Contact")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Form layout for QSO details
        form_layout = QFormLayout()

        # Callsign (required)
        self.callsign_input = QLineEdit()
        self.callsign_input.setPlaceholderText("Required")
        form_layout.addRow("Callsign:", self.callsign_input)

        # Frequency (required)
        freq_layout = QHBoxLayout()
        self.frequency_input = QLineEdit()
        self.frequency_input.setPlaceholderText("e.g., 14.260")
        freq_layout.addWidget(self.frequency_input)

        # Add button to sync frequency from CAT
        self.sync_freq_button = QPushButton("Sync from Radio")
        self.sync_freq_button.clicked.connect(self.sync_from_cat)
        freq_layout.addWidget(self.sync_freq_button)
        form_layout.addRow("Frequency (MHz):", freq_layout)

        # Mode (required)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(self.MODES)
        self.mode_combo.setEditable(True)
        form_layout.addRow("Mode:", self.mode_combo)

        # Date and Time (auto-filled with current UTC)
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("YYYYMMDD")
        form_layout.addRow("Date (UTC):", self.date_input)

        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText("HHMMSS")
        form_layout.addRow("Time (UTC):", self.time_input)

        # RST Sent/Received
        rst_layout = QHBoxLayout()
        self.rst_sent_input = QLineEdit("59")
        self.rst_sent_input.setMaximumWidth(60)
        rst_layout.addWidget(QLabel("Sent:"))
        rst_layout.addWidget(self.rst_sent_input)
        rst_layout.addSpacing(20)
        self.rst_rcvd_input = QLineEdit("59")
        self.rst_rcvd_input.setMaximumWidth(60)
        rst_layout.addWidget(QLabel("Rcvd:"))
        rst_layout.addWidget(self.rst_rcvd_input)
        rst_layout.addStretch()
        form_layout.addRow("RST:", rst_layout)

        # Park Reference
        self.park_input = QLineEdit()
        self.park_input.setPlaceholderText("e.g., K-0001")
        form_layout.addRow("Park Reference:", self.park_input)

        # Grid Square
        self.grid_input = QLineEdit()
        self.grid_input.setPlaceholderText("e.g., FN31pr")
        form_layout.addRow("Grid Square:", self.grid_input)

        # Name
        self.name_input = QLineEdit()
        form_layout.addRow("Name:", self.name_input)

        # QTH (Location)
        self.qth_input = QLineEdit()
        form_layout.addRow("QTH:", self.qth_input)

        # State
        self.state_input = QLineEdit()
        self.state_input.setMaximumWidth(60)
        form_layout.addRow("State:", self.state_input)

        # My Grid Square
        self.my_grid_input = QLineEdit()
        self.my_grid_input.setPlaceholderText("Your grid square")
        form_layout.addRow("My Grid Square:", self.my_grid_input)

        # Comments
        self.comment_input = QTextEdit()
        self.comment_input.setMaximumHeight(60)
        form_layout.addRow("Comments:", self.comment_input)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_button = QPushButton("Save QSO")
        self.save_button.clicked.connect(self.save_qso)
        self.save_button.setDefault(True)
        button_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def prefill_data(self):
        """Prefill form with spot data and station info"""
        # Fill contacted station data from spot
        if 'callsign' in self.spot_data:
            self.callsign_input.setText(self.spot_data['callsign'])

        # Fill frequency
        frequency_mhz = None
        if 'frequency' in self.spot_data:
            self.frequency_input.setText(self.spot_data['frequency'])
            try:
                frequency_mhz = float(self.spot_data['frequency'])
            except (ValueError, TypeError):
                frequency_mhz = None

        # Fill mode - resolve SSB/digital modes to appropriate sideband based on frequency
        if 'mode' in self.spot_data:
            mode = self.spot_data['mode']

            # Resolve mode based on frequency (SSB → USB/LSB, FT8/FT4/etc → DATA-U/DATA-L)
            # This conversion is for display in the logging dialog
            # The actual mode sent to the radio will be converted in sync_from_cat
            # For now, keep the original mode in the dialog so user sees what they expect
            index = self.mode_combo.findText(mode)
            if index >= 0:
                self.mode_combo.setCurrentIndex(index)
            else:
                self.mode_combo.setCurrentText(mode)

        # Fill park reference
        if 'park' in self.spot_data:
            self.park_input.setText(self.spot_data['park'])

        # Fill QTH from location
        if 'location' in self.spot_data:
            self.qth_input.setText(self.spot_data['location'])

        # Fill name from QRZ lookup
        if 'name' in self.spot_data:
            self.name_input.setText(self.spot_data['name'])

        # Fill current UTC date and time
        now = datetime.utcnow()
        self.date_input.setText(now.strftime("%Y%m%d"))
        self.time_input.setText(now.strftime("%H%M%S"))

        # Load and prefill MY station information from settings
        my_gridsquare = self.settings.value("station/my_gridsquare", "")
        if my_gridsquare:
            self.my_grid_input.setText(my_gridsquare)

        # Enable/disable sync button based on CAT availability
        if self.cat_service and self.cat_service.is_connected:
            self.sync_freq_button.setEnabled(True)
        else:
            self.sync_freq_button.setEnabled(False)
            self.sync_freq_button.setToolTip("CAT control not connected")

    def sync_from_cat(self):
        """Sync frequency and mode from CAT control"""
        if not self.cat_service or not self.cat_service.is_connected:
            QMessageBox.warning(
                self,
                "CAT Not Connected",
                "CAT control is not connected. Please configure and connect your radio in Settings."
            )
            return

        # Get frequency from radio
        freq = self.cat_service.get_frequency()
        if freq:
            freq_mhz = freq / 1_000_000
            self.frequency_input.setText(f"{freq_mhz:.6f}")

        # Get mode from radio
        mode = self.cat_service.get_mode()
        if mode:
            # Map mode to logging dialog modes
            mode_upper = mode.upper()
            # Try to find exact match first
            index = self.mode_combo.findText(mode_upper)
            if index >= 0:
                self.mode_combo.setCurrentIndex(index)
            else:
                # Try to set as text (will add to combo if editable)
                self.mode_combo.setEditText(mode_upper)

    def save_qso(self):
        """Validate and save the QSO"""
        # Validate required fields
        if not self.callsign_input.text().strip():
            QMessageBox.warning(self, "Invalid Input", "Callsign is required")
            self.callsign_input.setFocus()
            return

        if not self.frequency_input.text().strip():
            QMessageBox.warning(self, "Invalid Input", "Frequency is required")
            self.frequency_input.setFocus()
            return

        if not self.mode_combo.currentText().strip():
            QMessageBox.warning(self, "Invalid Input", "Mode is required")
            self.mode_combo.setFocus()
            return

        if not self.date_input.text().strip():
            QMessageBox.warning(self, "Invalid Input", "Date is required")
            self.date_input.setFocus()
            return

        if not self.time_input.text().strip():
            QMessageBox.warning(self, "Invalid Input", "Time is required")
            self.time_input.setFocus()
            return

        # Create QSO object
        try:
            # Load station information from settings
            my_callsign = self.settings.value("station/my_callsign", None)
            operator = self.settings.value("station/operator", None)
            my_gridsquare = self.my_grid_input.text().strip().upper() or self.settings.value("station/my_gridsquare", None)
            my_city = self.settings.value("station/my_city", None)
            my_state = self.settings.value("station/my_state", None)
            my_county = self.settings.value("station/my_county", None)
            my_country = self.settings.value("station/my_country", None)
            my_dxcc = self.settings.value("station/my_dxcc", None)
            my_lat = self.settings.value("station/my_lat", None)
            my_lon = self.settings.value("station/my_lon", None)
            my_postal_code = self.settings.value("station/my_postal_code", None)
            my_street = self.settings.value("station/my_street", None)
            my_rig = self.settings.value("station/my_rig", None)
            tx_pwr = self.settings.value("station/tx_pwr", None)
            ant_az = self.settings.value("station/ant_az", None)

            qso = QSO(
                callsign=self.callsign_input.text().strip().upper(),
                frequency=self.frequency_input.text().strip(),
                mode=self.mode_combo.currentText().strip().upper(),
                qso_date=self.date_input.text().strip(),
                time_on=self.time_input.text().strip(),
                rst_sent=self.rst_sent_input.text().strip(),
                rst_rcvd=self.rst_rcvd_input.text().strip(),
                park_reference=self.park_input.text().strip().upper() or None,
                gridsquare=self.grid_input.text().strip().upper() or None,
                name=self.name_input.text().strip() or None,
                qth=self.qth_input.text().strip() or None,
                state=self.state_input.text().strip().upper() or None,
                comment=self.comment_input.toPlainText().strip() or None,
                band=QSO.frequency_to_band(self.frequency_input.text().strip()),
                sig="POTA" if self.park_input.text().strip() else None,
                sig_info=self.park_input.text().strip().upper() or None,
                # My station information from settings
                my_callsign=my_callsign,
                operator=operator,
                my_gridsquare=my_gridsquare,
                my_city=my_city,
                my_state=my_state,
                my_county=my_county,
                my_country=my_country,
                my_dxcc=my_dxcc,
                my_lat=my_lat,
                my_lon=my_lon,
                my_postal_code=my_postal_code,
                my_street=my_street,
                my_rig=my_rig,
                tx_pwr=tx_pwr,
                ant_az=ant_az
            )

            # Save to database
            qso_id = self.db_manager.add_qso(qso)
            qso.id = qso_id

            # Check if auto-upload is enabled
            auto_upload = self.settings.value("qrz/auto_upload", False, type=bool)
            api_key = self.settings.value("qrz/api_key", "")

            upload_message = ""
            if auto_upload and api_key:
                try:
                    from potahunter.services.qrz_upload import QRZUploadService
                    upload_service = QRZUploadService(api_key)
                    result = upload_service.upload_qso(qso)

                    if result['success']:
                        # Mark as uploaded in database
                        qso.qrz_uploaded = True
                        qso.qrz_upload_date = datetime.utcnow().strftime("%Y%m%d %H%M%S")
                        self.db_manager.update_qso(qso)
                        upload_message = "\n\nUploaded to QRZ Logbook successfully!"
                    else:
                        upload_message = f"\n\nQRZ Upload failed: {result['message']}"
                except Exception as e:
                    upload_message = f"\n\nQRZ Upload error: {str(e)}"

            QMessageBox.information(
                self,
                "QSO Saved",
                f"Contact with {qso.callsign} saved successfully!{upload_message}"
            )

            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save QSO: {str(e)}"
            )
