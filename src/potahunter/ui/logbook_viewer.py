"""
Logbook viewer window for viewing and managing QSO records
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QStatusBar, QLabel, QMessageBox, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush, QAction

from potahunter.models.database import DatabaseManager


class LogbookViewer(QMainWindow):
    """Window for viewing and managing the QSO logbook"""

    # Signal emitted when logbook is modified
    logbook_modified = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager()
        self.qsos = []
        self.init_ui()
        self.load_logbook()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Logbook")
        self.setGeometry(100, 100, 1000, 600)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("QSO Logbook")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title)

        self.count_label = QLabel()
        header_layout.addWidget(self.count_label)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Control buttons
        button_layout = QHBoxLayout()

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_logbook)
        button_layout.addWidget(self.refresh_button)

        button_layout.addStretch()

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)

        # QSO Table
        self.qso_table = QTableWidget()
        self.qso_table.setColumnCount(18)
        self.qso_table.setHorizontalHeaderLabels([
            "Date", "Time", "Callsign", "Frequency", "Mode", "Band",
            "RST Sent", "RST Rcvd", "Park", "Grid", "Name", "QTH",
            "State", "County", "My Call", "My Grid", "Comment", "QRZ"
        ])

        # Enable sorting
        self.qso_table.setSortingEnabled(True)

        # Resize columns
        header = self.qso_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Callsign
        header.setSectionResizeMode(10, QHeaderView.Stretch)  # Name
        header.setSectionResizeMode(16, QHeaderView.Stretch)  # Comment

        # Double-click handler
        self.qso_table.doubleClicked.connect(self.edit_qso)

        # Allow selection of full rows with multi-select
        self.qso_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.qso_table.setSelectionMode(QTableWidget.ExtendedSelection)

        # Enable context menu
        self.qso_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.qso_table.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.qso_table)

        # Instructions
        instructions = QLabel("Double-click to edit • Right-click for options • Ctrl/Cmd+Click to select multiple • ✓ = Uploaded to QRZ")
        instructions.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(instructions)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def load_logbook(self):
        """Load all QSOs from the database"""
        self.status_bar.showMessage("Loading logbook...")

        try:
            # Get all QSOs from database
            self.qsos = self.db_manager.get_all_qsos()

            # Populate table
            self.populate_table()

            # Update count
            self.count_label.setText(f"Total QSOs: {len(self.qsos)}")
            self.status_bar.showMessage(f"Loaded {len(self.qsos)} QSOs", 3000)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load logbook: {str(e)}"
            )
            self.status_bar.showMessage("Error loading logbook", 3000)

    def populate_table(self):
        """Populate the table with QSO data"""
        self.qso_table.setSortingEnabled(False)
        self.qso_table.setRowCount(len(self.qsos))

        for row, qso in enumerate(self.qsos):
            # Format date (YYYYMMDD -> YYYY-MM-DD)
            date_str = qso.qso_date
            if len(date_str) == 8:
                formatted_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
            else:
                formatted_date = date_str

            # Format time (HHMMSS -> HH:MM:SS)
            time_str = qso.time_on
            if len(time_str) == 6:
                formatted_time = f"{time_str[0:2]}:{time_str[2:4]}:{time_str[4:6]}"
            elif len(time_str) == 4:
                formatted_time = f"{time_str[0:2]}:{time_str[2:4]}"
            else:
                formatted_time = time_str

            # Create items
            date_item = QTableWidgetItem(formatted_date)
            time_item = QTableWidgetItem(formatted_time)
            callsign_item = QTableWidgetItem(qso.callsign)
            freq_item = QTableWidgetItem(qso.frequency)
            mode_item = QTableWidgetItem(qso.mode)
            band_item = QTableWidgetItem(qso.band or "")
            rst_sent_item = QTableWidgetItem(qso.rst_sent or "")
            rst_rcvd_item = QTableWidgetItem(qso.rst_rcvd or "")
            park_item = QTableWidgetItem(qso.park_reference or "")
            grid_item = QTableWidgetItem(qso.gridsquare or "")
            name_item = QTableWidgetItem(qso.name or "")
            qth_item = QTableWidgetItem(qso.qth or "")
            state_item = QTableWidgetItem(qso.state or "")
            county_item = QTableWidgetItem(qso.county or "")
            my_call_item = QTableWidgetItem(qso.my_callsign or "")
            my_grid_item = QTableWidgetItem(qso.my_gridsquare or "")
            comment_item = QTableWidgetItem(qso.comment or "")

            # QRZ upload status
            qrz_item = QTableWidgetItem("✓" if qso.qrz_uploaded else "")
            qrz_item.setTextAlignment(Qt.AlignCenter)
            if qso.qrz_uploaded:
                qrz_item.setForeground(QBrush(QColor(0, 128, 0)))  # Green

            # Store QSO ID in the first column for later reference
            date_item.setData(Qt.UserRole, qso.id)

            # Highlight POTA contacts
            items = [
                date_item, time_item, callsign_item, freq_item, mode_item, band_item,
                rst_sent_item, rst_rcvd_item, park_item, grid_item, name_item, qth_item,
                state_item, county_item, my_call_item, my_grid_item, comment_item, qrz_item
            ]

            if qso.park_reference:
                color = QColor(255, 250, 205)  # Light yellow
                brush = QBrush(color)
                for item in items:
                    item.setBackground(brush)

            # Set items in table
            self.qso_table.setItem(row, 0, date_item)
            self.qso_table.setItem(row, 1, time_item)
            self.qso_table.setItem(row, 2, callsign_item)
            self.qso_table.setItem(row, 3, freq_item)
            self.qso_table.setItem(row, 4, mode_item)
            self.qso_table.setItem(row, 5, band_item)
            self.qso_table.setItem(row, 6, rst_sent_item)
            self.qso_table.setItem(row, 7, rst_rcvd_item)
            self.qso_table.setItem(row, 8, park_item)
            self.qso_table.setItem(row, 9, grid_item)
            self.qso_table.setItem(row, 10, name_item)
            self.qso_table.setItem(row, 11, qth_item)
            self.qso_table.setItem(row, 12, state_item)
            self.qso_table.setItem(row, 13, county_item)
            self.qso_table.setItem(row, 14, my_call_item)
            self.qso_table.setItem(row, 15, my_grid_item)
            self.qso_table.setItem(row, 16, comment_item)
            self.qso_table.setItem(row, 17, qrz_item)

        self.qso_table.setSortingEnabled(True)
        # Sort by date and time (most recent first)
        self.qso_table.sortItems(0, Qt.DescendingOrder)

    def edit_qso(self, index):
        """
        Open edit dialog for selected QSO

        Args:
            index: Table index of double-clicked item
        """
        row = index.row()
        if row < 0:
            return

        # Get QSO ID from the first column
        qso_id = self.qso_table.item(row, 0).data(Qt.UserRole)

        # Find the QSO object
        qso = None
        for q in self.qsos:
            if q.id == qso_id:
                qso = q
                break

        if not qso:
            QMessageBox.warning(self, "Error", "Could not find QSO record")
            return

        # Import and show edit dialog
        from potahunter.ui.qso_edit_dialog import QSOEditDialog
        dialog = QSOEditDialog(qso, self)

        if dialog.exec():
            # Reload logbook if changes were made
            self.load_logbook()
            self.logbook_modified.emit()
            self.status_bar.showMessage("Logbook updated", 3000)

    def show_context_menu(self, position):
        """
        Show context menu when right-clicking on table

        Args:
            position: Position where right-click occurred
        """
        # Get selected rows
        selected_rows = self.qso_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        # Create context menu
        menu = QMenu(self)

        # Edit action (only if single selection)
        if len(selected_rows) == 1:
            edit_action = QAction("Edit QSO", self)
            edit_action.triggered.connect(lambda: self.edit_qso(selected_rows[0]))
            menu.addAction(edit_action)
            menu.addSeparator()

        # Delete action
        if len(selected_rows) == 1:
            delete_action = QAction("Delete QSO", self)
            delete_action.triggered.connect(self.delete_selected_qsos)
            menu.addAction(delete_action)
        else:
            delete_action = QAction(f"Delete {len(selected_rows)} QSOs", self)
            delete_action.triggered.connect(self.delete_selected_qsos)
            menu.addAction(delete_action)

        # Show menu at cursor position
        menu.exec(self.qso_table.viewport().mapToGlobal(position))

    def delete_selected_qsos(self):
        """Delete all selected QSOs after confirmation"""
        selected_rows = self.qso_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        # Get QSO IDs and callsigns for selected rows
        qsos_to_delete = []
        for index in selected_rows:
            row = index.row()
            qso_id = self.qso_table.item(row, 0).data(Qt.UserRole)
            callsign = self.qso_table.item(row, 2).text()
            date = self.qso_table.item(row, 0).text()
            time = self.qso_table.item(row, 1).text()
            qsos_to_delete.append({
                'id': qso_id,
                'callsign': callsign,
                'date': date,
                'time': time
            })

        # Confirmation dialog
        if len(qsos_to_delete) == 1:
            qso = qsos_to_delete[0]
            message = (
                f"Are you sure you want to delete this contact?\n\n"
                f"Callsign: {qso['callsign']}\n"
                f"Date: {qso['date']}\n"
                f"Time: {qso['time']}\n\n"
                f"This action cannot be undone."
            )
        else:
            callsigns = ", ".join([q['callsign'] for q in qsos_to_delete[:5]])
            if len(qsos_to_delete) > 5:
                callsigns += f", ... (+{len(qsos_to_delete) - 5} more)"
            message = (
                f"Are you sure you want to delete {len(qsos_to_delete)} contacts?\n\n"
                f"Callsigns: {callsigns}\n\n"
                f"This action cannot be undone."
            )

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Delete all selected QSOs
            deleted_count = 0
            failed_count = 0

            for qso in qsos_to_delete:
                try:
                    if self.db_manager.delete_qso(qso['id']):
                        deleted_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    failed_count += 1

            # Show result message
            if failed_count == 0:
                if deleted_count == 1:
                    QMessageBox.information(self, "Success", "QSO deleted successfully")
                else:
                    QMessageBox.information(self, "Success", f"{deleted_count} QSOs deleted successfully")

                # Reload logbook
                self.load_logbook()
                self.logbook_modified.emit()
                self.status_bar.showMessage(f"Deleted {deleted_count} QSO(s)", 3000)
            else:
                QMessageBox.warning(
                    self,
                    "Partial Success",
                    f"Deleted {deleted_count} QSO(s), but {failed_count} failed to delete"
                )
                self.load_logbook()
                self.logbook_modified.emit()