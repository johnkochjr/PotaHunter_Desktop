"""
Logging dialog for entering QSO details
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QMessageBox,
    QComboBox, QTextEdit
)
from PySide6.QtCore import Qt
from datetime import datetime

from potahunter.models.qso import QSO
from potahunter.models.database import DatabaseManager


class LoggingDialog(QDialog):
    """Dialog for logging a QSO with prefilled spot data"""

    # Common amateur radio modes
    MODES = ["SSB", "CW", "FM", "AM", "RTTY", "PSK31", "FT8", "FT4", "JS8"]

    def __init__(self, spot_data: dict, parent=None):
        super().__init__(parent)
        self.spot_data = spot_data
        self.db_manager = DatabaseManager()
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
        self.frequency_input = QLineEdit()
        self.frequency_input.setPlaceholderText("e.g., 14.260")
        form_layout.addRow("Frequency (MHz):", self.frequency_input)

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
        """Prefill form with spot data"""
        # Fill callsign
        if 'callsign' in self.spot_data:
            self.callsign_input.setText(self.spot_data['callsign'])

        # Fill frequency
        if 'frequency' in self.spot_data:
            self.frequency_input.setText(self.spot_data['frequency'])

        # Fill mode
        if 'mode' in self.spot_data:
            mode = self.spot_data['mode']
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

        # TODO: Calculate grid square from park location
        # This would require geocoding the park location or maintaining a lookup table

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
                my_gridsquare=self.my_grid_input.text().strip().upper() or None,
                band=QSO.frequency_to_band(self.frequency_input.text().strip()),
                sig="POTA" if self.park_input.text().strip() else None,
                sig_info=self.park_input.text().strip().upper() or None
            )

            # Save to database
            qso_id = self.db_manager.add_qso(qso)

            QMessageBox.information(
                self,
                "QSO Saved",
                f"Contact with {qso.callsign} saved successfully!"
            )

            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save QSO: {str(e)}"
            )
