"""
QSO edit dialog for modifying or deleting QSO records
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


class QSOEditDialog(QDialog):
    """Dialog for editing or deleting a QSO"""

    # Common amateur radio modes
    MODES = ["SSB", "CW", "FM", "AM", "RTTY", "PSK31", "FT8", "FT4", "JS8"]

    def __init__(self, qso: QSO, parent=None):
        super().__init__(parent)
        self.qso = qso
        self.db_manager = DatabaseManager()
        self.init_ui()
        self.load_qso_data()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle(f"Edit QSO - {self.qso.callsign}")
        self.setModal(True)
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Title
        title = QLabel(f"Edit Contact with {self.qso.callsign}")
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

        # Date and Time
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("YYYYMMDD")
        form_layout.addRow("Date (UTC):", self.date_input)

        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText("HHMMSS")
        form_layout.addRow("Time (UTC):", self.time_input)

        # RST Sent/Received
        rst_layout = QHBoxLayout()
        self.rst_sent_input = QLineEdit()
        self.rst_sent_input.setMaximumWidth(60)
        rst_layout.addWidget(QLabel("Sent:"))
        rst_layout.addWidget(self.rst_sent_input)
        rst_layout.addSpacing(20)
        self.rst_rcvd_input = QLineEdit()
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

        # Delete button on the left
        self.delete_button = QPushButton("Delete QSO")
        self.delete_button.clicked.connect(self.delete_qso)
        self.delete_button.setStyleSheet("background-color: #d9534f; color: white;")
        button_layout.addWidget(self.delete_button)

        button_layout.addStretch()

        # Save and Cancel on the right
        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_qso)
        self.save_button.setDefault(True)
        button_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def load_qso_data(self):
        """Load existing QSO data into the form"""
        self.callsign_input.setText(self.qso.callsign)
        self.frequency_input.setText(self.qso.frequency)

        # Set mode
        mode = self.qso.mode
        index = self.mode_combo.findText(mode)
        if index >= 0:
            self.mode_combo.setCurrentIndex(index)
        else:
            self.mode_combo.setCurrentText(mode)

        self.date_input.setText(self.qso.qso_date)
        self.time_input.setText(self.qso.time_on)
        self.rst_sent_input.setText(self.qso.rst_sent or "")
        self.rst_rcvd_input.setText(self.qso.rst_rcvd or "")
        self.park_input.setText(self.qso.park_reference or "")
        self.grid_input.setText(self.qso.gridsquare or "")
        self.name_input.setText(self.qso.name or "")
        self.qth_input.setText(self.qso.qth or "")
        self.state_input.setText(self.qso.state or "")
        self.my_grid_input.setText(self.qso.my_gridsquare or "")
        self.comment_input.setPlainText(self.qso.comment or "")

    def save_qso(self):
        """Validate and save the updated QSO"""
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

        # Update QSO object
        try:
            self.qso.callsign = self.callsign_input.text().strip().upper()
            self.qso.frequency = self.frequency_input.text().strip()
            self.qso.mode = self.mode_combo.currentText().strip().upper()
            self.qso.qso_date = self.date_input.text().strip()
            self.qso.time_on = self.time_input.text().strip()
            self.qso.rst_sent = self.rst_sent_input.text().strip() or None
            self.qso.rst_rcvd = self.rst_rcvd_input.text().strip() or None
            self.qso.park_reference = self.park_input.text().strip().upper() or None
            self.qso.gridsquare = self.grid_input.text().strip().upper() or None
            self.qso.name = self.name_input.text().strip() or None
            self.qso.qth = self.qth_input.text().strip() or None
            self.qso.state = self.state_input.text().strip().upper() or None
            self.qso.comment = self.comment_input.toPlainText().strip() or None
            self.qso.my_gridsquare = self.my_grid_input.text().strip().upper() or None
            self.qso.band = QSO.frequency_to_band(self.frequency_input.text().strip())
            self.qso.sig = "POTA" if self.park_input.text().strip() else None
            self.qso.sig_info = self.park_input.text().strip().upper() or None

            # Update in database
            self.db_manager.update_qso(self.qso)

            QMessageBox.information(
                self,
                "QSO Updated",
                f"Contact with {self.qso.callsign} updated successfully!"
            )

            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to update QSO: {str(e)}"
            )

    def delete_qso(self):
        """Delete the QSO after confirmation"""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete this contact with {self.qso.callsign}?\n\n"
            f"Date: {self.qso.qso_date}\n"
            f"Time: {self.qso.time_on}\n"
            f"Frequency: {self.qso.frequency}\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.db_manager.delete_qso(self.qso.id)
                QMessageBox.information(
                    self,
                    "QSO Deleted",
                    f"Contact with {self.qso.callsign} has been deleted."
                )
                self.accept()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to delete QSO: {str(e)}"
                )