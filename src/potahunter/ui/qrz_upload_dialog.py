"""
QRZ Logbook upload dialog
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QProgressBar, QMessageBox, QCheckBox, QLineEdit, QFormLayout,
    QWidget
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QBrush
from typing import List
from datetime import datetime

from potahunter.models.qso import QSO
from potahunter.models.database import DatabaseManager
from potahunter.services.qrz_upload import QRZUploadService


class UploadWorker(QThread):
    """Worker thread for uploading QSOs"""

    progress = Signal(int, int, str)  # current, total, message
    finished = Signal(dict)  # results

    def __init__(self, qsos: List[QSO], api_key: str, station_callsign: str):
        super().__init__()
        self.qsos = qsos
        self.api_key = api_key
        self.station_callsign = station_callsign
        self.db_manager = DatabaseManager()

    def run(self):
        """Upload QSOs in background thread"""
        upload_service = QRZUploadService(self.api_key)

        results = {
            'total': len(self.qsos),
            'success': 0,
            'failed': 0,
            'duplicate': 0,
            'errors': []
        }

        for index, qso in enumerate(self.qsos):
            # Upload QSO
            result = upload_service.upload_qso(qso, self.station_callsign)

            # Update progress
            self.progress.emit(index + 1, len(self.qsos),
                             f"Uploading {qso.callsign}...")

            if result['success']:
                results['success'] += 1
                # Mark as uploaded in database
                qso.qrz_uploaded = True
                qso.qrz_upload_date = datetime.utcnow().strftime("%Y%m%d %H%M%S")
                self.db_manager.update_qso(qso)
            else:
                results['failed'] += 1
                if 'DUPLICATE' in result.get('response', ''):
                    results['duplicate'] += 1
                    # Also mark duplicates as uploaded
                    qso.qrz_uploaded = True
                    qso.qrz_upload_date = datetime.utcnow().strftime("%Y%m%d %H%M%S")
                    self.db_manager.update_qso(qso)

                results['errors'].append({
                    'callsign': qso.callsign,
                    'date': qso.qso_date,
                    'time': qso.time_on,
                    'message': result['message']
                })

        self.finished.emit(results)


class QRZUploadDialog(QDialog):
    """Dialog for uploading QSOs to QRZ Logbook"""

    def __init__(self, qsos: List[QSO], api_key: str, parent=None):
        super().__init__(parent)
        self.qsos = qsos
        self.api_key = api_key
        self.selected_qsos = []
        self.upload_worker = None
        self.init_ui()
        self.populate_table()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Upload to QRZ Logbook")
        self.setModal(True)
        self.setMinimumSize(900, 600)

        layout = QVBoxLayout(self)

        # Header
        header = QLabel("<h2>Upload QSOs to QRZ Logbook</h2>")
        layout.addWidget(header)

        # Station callsign input
        station_form = QFormLayout()
        self.station_callsign = QLineEdit()
        self.station_callsign.setPlaceholderText("Leave blank to use QRZ account callsign")
        self.station_callsign.setMaximumWidth(200)
        station_form.addRow("Station Callsign (optional):", self.station_callsign)
        layout.addLayout(station_form)

        # Selection buttons
        selection_layout = QHBoxLayout()

        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self.select_all)
        selection_layout.addWidget(self.select_all_button)

        self.select_none_button = QPushButton("Select None")
        self.select_none_button.clicked.connect(self.select_none)
        selection_layout.addWidget(self.select_none_button)

        self.select_unuploaded_button = QPushButton("Select Unuploaded")
        self.select_unuploaded_button.clicked.connect(self.select_unuploaded)
        selection_layout.addWidget(self.select_unuploaded_button)

        selection_layout.addStretch()

        self.selection_count_label = QLabel()
        selection_layout.addWidget(self.selection_count_label)

        layout.addLayout(selection_layout)

        # QSO Table
        self.qso_table = QTableWidget()
        self.qso_table.setColumnCount(8)
        self.qso_table.setHorizontalHeaderLabels([
            "Select", "Date", "Time", "Callsign", "Frequency",
            "Mode", "Park", "Uploaded"
        ])

        # Resize columns
        header = self.qso_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Select
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Date
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Time
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Callsign
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Frequency
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Mode
        header.setSectionResizeMode(6, QHeaderView.Stretch)  # Park
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Uploaded

        self.qso_table.itemChanged.connect(self.update_selection_count)

        layout.addWidget(self.qso_table)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.progress_label = QLabel()
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.upload_button = QPushButton("Upload Selected")
        self.upload_button.clicked.connect(self.upload_qsos)
        self.upload_button.setStyleSheet("background-color: #5cb85c; color: white; font-weight: bold;")
        button_layout.addWidget(self.upload_button)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.reject)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)

    def populate_table(self):
        """Populate the table with QSO data"""
        self.qso_table.setRowCount(len(self.qsos))

        for row, qso in enumerate(self.qsos):
            # Checkbox for selection
            checkbox = QCheckBox()
            checkbox.setChecked(not qso.qrz_uploaded)  # Auto-select unuploaded
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.qso_table.setCellWidget(row, 0, checkbox_widget)

            # Format date (YYYYMMDD -> YYYY-MM-DD)
            date_str = qso.qso_date
            if len(date_str) == 8:
                formatted_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
            else:
                formatted_date = date_str

            # Format time (HHMMSS -> HH:MM)
            time_str = qso.time_on
            if len(time_str) >= 4:
                formatted_time = f"{time_str[0:2]}:{time_str[2:4]}"
            else:
                formatted_time = time_str

            # Create items
            date_item = QTableWidgetItem(formatted_date)
            time_item = QTableWidgetItem(formatted_time)
            callsign_item = QTableWidgetItem(qso.callsign)
            freq_item = QTableWidgetItem(qso.frequency)
            mode_item = QTableWidgetItem(qso.mode)
            park_item = QTableWidgetItem(qso.park_reference or "")
            uploaded_item = QTableWidgetItem("✓" if qso.qrz_uploaded else "")

            # Make items read-only
            for item in [date_item, time_item, callsign_item, freq_item, mode_item, park_item, uploaded_item]:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            # Highlight already uploaded
            if qso.qrz_uploaded:
                color = QColor(200, 230, 200)  # Light green
                brush = QBrush(color)
                date_item.setBackground(brush)
                time_item.setBackground(brush)
                callsign_item.setBackground(brush)
                freq_item.setBackground(brush)
                mode_item.setBackground(brush)
                park_item.setBackground(brush)
                uploaded_item.setBackground(brush)

            # Set items in table
            self.qso_table.setItem(row, 1, date_item)
            self.qso_table.setItem(row, 2, time_item)
            self.qso_table.setItem(row, 3, callsign_item)
            self.qso_table.setItem(row, 4, freq_item)
            self.qso_table.setItem(row, 5, mode_item)
            self.qso_table.setItem(row, 6, park_item)
            self.qso_table.setItem(row, 7, uploaded_item)

        self.update_selection_count()

    def select_all(self):
        """Select all QSOs"""
        for row in range(self.qso_table.rowCount()):
            checkbox_widget = self.qso_table.cellWidget(row, 0)
            checkbox = checkbox_widget.findChild(QCheckBox)
            if checkbox:
                checkbox.setChecked(True)
        self.update_selection_count()

    def select_none(self):
        """Deselect all QSOs"""
        for row in range(self.qso_table.rowCount()):
            checkbox_widget = self.qso_table.cellWidget(row, 0)
            checkbox = checkbox_widget.findChild(QCheckBox)
            if checkbox:
                checkbox.setChecked(False)
        self.update_selection_count()

    def select_unuploaded(self):
        """Select only unuploaded QSOs"""
        for row in range(self.qso_table.rowCount()):
            qso = self.qsos[row]
            checkbox_widget = self.qso_table.cellWidget(row, 0)
            checkbox = checkbox_widget.findChild(QCheckBox)
            if checkbox:
                checkbox.setChecked(not qso.qrz_uploaded)
        self.update_selection_count()

    def update_selection_count(self):
        """Update the selection count label"""
        count = 0
        for row in range(self.qso_table.rowCount()):
            checkbox_widget = self.qso_table.cellWidget(row, 0)
            checkbox = checkbox_widget.findChild(QCheckBox)
            if checkbox and checkbox.isChecked():
                count += 1

        self.selection_count_label.setText(f"{count} QSO(s) selected")

    def get_selected_qsos(self) -> List[QSO]:
        """Get list of selected QSOs"""
        selected = []
        for row in range(self.qso_table.rowCount()):
            checkbox_widget = self.qso_table.cellWidget(row, 0)
            checkbox = checkbox_widget.findChild(QCheckBox)
            if checkbox and checkbox.isChecked():
                selected.append(self.qsos[row])
        return selected

    def upload_qsos(self):
        """Upload selected QSOs to QRZ"""
        selected_qsos = self.get_selected_qsos()

        if not selected_qsos:
            QMessageBox.warning(
                self,
                "No QSOs Selected",
                "Please select at least one QSO to upload."
            )
            return

        # Confirm upload
        reply = QMessageBox.question(
            self,
            "Confirm Upload",
            f"Upload {len(selected_qsos)} QSO(s) to QRZ Logbook?\n\n"
            "This will mark them as uploaded in your local database.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply != QMessageBox.Yes:
            return

        # Disable buttons during upload
        self.upload_button.setEnabled(False)
        self.select_all_button.setEnabled(False)
        self.select_none_button.setEnabled(False)
        self.select_unuploaded_button.setEnabled(False)
        self.close_button.setEnabled(False)

        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(selected_qsos))
        self.progress_bar.setValue(0)
        self.progress_label.setVisible(True)
        self.progress_label.setText("Starting upload...")

        # Get station callsign
        station_callsign = self.station_callsign.text().strip() or None

        # Start upload in background thread
        self.upload_worker = UploadWorker(selected_qsos, self.api_key, station_callsign)
        self.upload_worker.progress.connect(self.on_progress)
        self.upload_worker.finished.connect(self.on_finished)
        self.upload_worker.start()

    def on_progress(self, current: int, total: int, message: str):
        """Handle progress updates"""
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"{message} ({current}/{total})")

    def on_finished(self, results: dict):
        """Handle upload completion"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)

        # Re-enable buttons
        self.upload_button.setEnabled(True)
        self.select_all_button.setEnabled(True)
        self.select_none_button.setEnabled(True)
        self.select_unuploaded_button.setEnabled(True)
        self.close_button.setEnabled(True)

        # Show results
        success_count = results['success']
        failed_count = results['failed']
        duplicate_count = results['duplicate']
        total_count = results['total']

        message = f"Upload Complete!\n\n"
        message += f"Total: {total_count}\n"
        message += f"Success: {success_count}\n"
        message += f"Duplicates: {duplicate_count}\n"
        message += f"Failed: {failed_count - duplicate_count}\n"

        if results['errors']:
            message += "\nErrors:\n"
            for error in results['errors'][:5]:  # Show first 5 errors
                message += f"- {error['callsign']} ({error['date']}): {error['message']}\n"
            if len(results['errors']) > 5:
                message += f"... and {len(results['errors']) - 5} more\n"

        if failed_count > 0:
            QMessageBox.warning(self, "Upload Completed with Errors", message)
        else:
            QMessageBox.information(self, "Upload Successful", message)

        # Refresh table
        self.populate_table()

        # If all succeeded, close dialog
        if failed_count == 0:
            self.accept()
