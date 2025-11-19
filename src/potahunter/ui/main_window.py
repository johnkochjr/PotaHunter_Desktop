"""
Main window for POTA Hunter application
"""

import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QStatusBar, QMenuBar, QMenu, QComboBox, QLabel, QCheckBox,
    QTextEdit, QGroupBox, QSplitter, QSizePolicy, QScrollArea, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QUrl, QSettings, QByteArray
from PySide6.QtGui import QAction, QColor, QBrush, QDesktopServices, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from potahunter.services.pota_api import PotaAPIService
from potahunter.services.qrz_api import QRZAPIService
from potahunter.services.cat_service import CATService
from potahunter.ui.logging_dialog import LoggingDialog, resolve_mode_for_radio
from potahunter.ui.settings_dialog import SettingsDialog
from potahunter.ui.logbook_viewer import LogbookViewer
from potahunter.models.database import DatabaseManager
from potahunter.utils.adif_export import ADIFExporter

class MainWindow(QMainWindow):
    """Main application window displaying POTA spots"""

    # Mode color definitions
    MODE_COLORS = {
        'CW': QColor(173, 216, 230),      # Light blue
        'FT8': QColor(144, 238, 144),     # Light green
        'FT4': QColor(144, 238, 144),     # Light green
        'RTTY': QColor(255, 218, 185),    # Peach
        'PSK31': QColor(255, 218, 185),   # Peach
        'SSB': QColor(255, 222, 173),     # Navajo white (phone)
        'USB': QColor(255, 222, 173),     # Navajo white (phone)
        'LSB': QColor(255, 222, 173),     # Navajo white (phone)
        'FM': QColor(255, 222, 173),      # Navajo white (phone)
        'AM': QColor(255, 222, 173),      # Navajo white (phone)
    }

    def __init__(self):
        super().__init__()
        self.pota_service = PotaAPIService()
        self.qrz_service = QRZAPIService()
        self.cat_service = CATService()
        self.db_manager = DatabaseManager()
        self.all_spots = []  # Store all spots for filtering
        self.all_qsos = []  # Store all QSOs for filtering
        self.settings = QSettings()
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.on_image_downloaded)
        self.current_qrz_info = {}  # Store current callsign's QRZ info
        self.load_qrz_credentials()
        self.init_ui()
        self.setup_refresh_timer()
        self.refresh_spots()
        self.refresh_logbook()  # Load logbook on startup

        # Connect CAT service signals
        self.cat_service.frequency_changed.connect(self.on_cat_frequency_changed)
        self.cat_service.mode_changed.connect(self.on_cat_mode_changed)
        self.cat_service.connection_status_changed.connect(self.on_cat_connection_status_changed)

        # Load CAT settings after UI is initialized (so status_bar exists)
        self.load_cat_settings()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("POTA Hunter - Spots & Logging")
        self.setGeometry(100, 100, 1400, 900)  # Increased size for logbook section

        # Create menu bar
        self.create_menus()

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout(central_widget)

        # Filter section
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filters:"))

        # Band filter
        filter_layout.addWidget(QLabel("Band:"))
        self.band_filter = QComboBox()
        self.band_filter.addItems([
            "All Bands", "160m", "80m", "60m", "40m", "30m",
            "20m", "17m", "15m", "12m", "10m", "6m", "2m"
        ])
        self.band_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.band_filter)

        # Mode filter
        filter_layout.addWidget(QLabel("Mode:"))
        self.mode_filter = QComboBox()
        self.mode_filter.addItems([
            "All Modes", "CW", "Digital", "Phone"
        ])
        self.mode_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.mode_filter)

        # Park/Callsign filter
        filter_layout.addWidget(QLabel("Search:"))
        self.search_filter = QComboBox()
        self.search_filter.setEditable(True)
        self.search_filter.setPlaceholderText("Park or Callsign...")
        self.search_filter.lineEdit().textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_filter)

        # Clear filters button
        clear_filter_btn = QPushButton("Clear Filters")
        clear_filter_btn.clicked.connect(self.clear_filters)
        filter_layout.addWidget(clear_filter_btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Control buttons
        button_layout = QHBoxLayout()

        self.refresh_button = QPushButton("Refresh Spots")
        self.refresh_button.clicked.connect(self.refresh_spots)
        button_layout.addWidget(self.refresh_button)

        self.auto_refresh_button = QPushButton("Auto-Refresh: ON")
        self.auto_refresh_button.setCheckable(True)
        self.auto_refresh_button.setChecked(True)
        self.auto_refresh_button.clicked.connect(self.toggle_auto_refresh)
        button_layout.addWidget(self.auto_refresh_button)

        # CAT status indicator
        self.cat_status_label = QLabel("CAT: Disconnected")
        self.cat_status_label.setStyleSheet("color: gray; padding: 5px;")
        button_layout.addWidget(self.cat_status_label)

        self.cat_freq_label = QLabel("")
        self.cat_freq_label.setStyleSheet("padding: 5px; font-weight: bold;")
        button_layout.addWidget(self.cat_freq_label)

        button_layout.addStretch()

        self.logbook_button = QPushButton("View Logbook")
        self.logbook_button.clicked.connect(self.open_logbook)
        button_layout.addWidget(self.logbook_button)

        self.export_button = QPushButton("Export Log (ADIF)")
        self.export_button.clicked.connect(self.export_log)
        button_layout.addWidget(self.export_button)

        self.upload_button = QPushButton("Upload to QRZ Logbook")
        self.upload_button.clicked.connect(self.upload_log)
        button_layout.addWidget(self.upload_button)

        layout.addLayout(button_layout)

        # Color legend
        legend_layout = QHBoxLayout()
        legend_layout.setContentsMargins(0, 0, 0, 0)  # Remove extra margins
        legend_layout.setSpacing(10)  # Adjust spacing between items
        legend_layout.addWidget(QLabel("Mode Colors:"))

        cw_label = QLabel(" CW ")
        cw_label.setStyleSheet("background-color: rgb(173, 216, 230); padding: 2px 8px; border-radius: 3px;")
        cw_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed) 
        legend_layout.addWidget(cw_label)

        digital_label = QLabel(" Digital ")
        digital_label.setStyleSheet("background-color: rgb(144, 238, 144); padding: 2px 8px; border-radius: 3px;")
        digital_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        legend_layout.addWidget(digital_label)

        phone_label = QLabel(" Phone ")
        phone_label.setStyleSheet("background-color: rgb(255, 222, 173); padding: 2px 8px; border-radius: 3px;")
        phone_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        legend_layout.addWidget(phone_label)

        legend_layout.addStretch()
        layout.addLayout(legend_layout)

        # Create main horizontal splitter for POTA spots/logbook and details panel
        main_splitter = QSplitter(Qt.Horizontal)

        # Create left side vertical splitter for POTA spots and logbook
        left_splitter = QSplitter(Qt.Vertical)

        # POTA Spots table section
        spots_widget = QWidget()
        spots_layout = QVBoxLayout(spots_widget)
        spots_layout.setContentsMargins(0, 0, 0, 0)

        spots_label = QLabel("POTA Spots")
        spots_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        spots_layout.addWidget(spots_label)

        self.spots_table = QTableWidget()
        self.spots_table.setColumnCount(7)
        self.spots_table.setHorizontalHeaderLabels([
            "Time", "Callsign", "Frequency", "Mode",
            "Park", "Location", "Spotter"
        ])

        # Make table sortable
        self.spots_table.setSortingEnabled(True)

        # Resize columns to content
        header = self.spots_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Park column
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # Location column

        # Double-click handler - different actions based on column
        self.spots_table.doubleClicked.connect(self.handle_table_double_click)

        # Single-click handler - lookup callsign info and filter logbook
        self.spots_table.currentItemChanged.connect(self.on_row_selection_changed)

        spots_layout.addWidget(self.spots_table)
        left_splitter.addWidget(spots_widget)

        # Logbook section
        logbook_widget = QWidget()
        logbook_layout = QVBoxLayout(logbook_widget)
        logbook_layout.setContentsMargins(0, 0, 0, 0)

        # Logbook header with filter dropdown
        logbook_header_layout = QHBoxLayout()
        logbook_label = QLabel("Logbook")
        logbook_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        logbook_header_layout.addWidget(logbook_label)

        self.logbook_count_label = QLabel("0 QSOs")
        self.logbook_count_label.setStyleSheet("color: gray; font-size: 11px;")
        logbook_header_layout.addWidget(self.logbook_count_label)

        logbook_header_layout.addSpacing(20)
        logbook_header_layout.addWidget(QLabel("Auto-Filter:"))

        self.logbook_filter_combo = QComboBox()
        self.logbook_filter_combo.addItems(["None", "Callsign", "Park"])
        self.logbook_filter_combo.setToolTip("Automatically filter logbook when clicking POTA spots")
        self.logbook_filter_combo.currentTextChanged.connect(self.on_logbook_filter_changed)
        logbook_header_layout.addWidget(self.logbook_filter_combo)

        logbook_header_layout.addStretch()

        # Refresh logbook button
        self.refresh_logbook_button = QPushButton("Refresh Logbook")
        self.refresh_logbook_button.clicked.connect(self.refresh_logbook)
        logbook_header_layout.addWidget(self.refresh_logbook_button)

        logbook_layout.addLayout(logbook_header_layout)

        # Logbook table
        self.logbook_table = QTableWidget()
        self.logbook_table.setColumnCount(13)
        self.logbook_table.setHorizontalHeaderLabels([
            "Date", "Time", "Callsign", "Frequency", "Mode", "Band",
            "RST Sent", "RST Rcvd", "Park", "Name", "QTH", "State", "Comment"
        ])

        # Enable sorting
        self.logbook_table.setSortingEnabled(True)

        # Resize columns
        logbook_header = self.logbook_table.horizontalHeader()
        logbook_header.setSectionResizeMode(QHeaderView.ResizeToContents)
        logbook_header.setSectionResizeMode(2, QHeaderView.Stretch)  # Callsign
        logbook_header.setSectionResizeMode(9, QHeaderView.Stretch)  # Name
        logbook_header.setSectionResizeMode(12, QHeaderView.Stretch)  # Comment

        # Allow selection of full rows
        self.logbook_table.setSelectionBehavior(QTableWidget.SelectRows)

        # Double-click to edit (opens full logbook viewer)
        self.logbook_table.doubleClicked.connect(self.open_logbook)

        logbook_layout.addWidget(self.logbook_table)

        left_splitter.addWidget(logbook_widget)

        # Set initial sizes for vertical splitter (60% POTA spots, 40% logbook)
        left_splitter.setSizes([600, 400])

        main_splitter.addWidget(left_splitter)

        # Details panel on the right
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)

        # Callsign info group
        callsign_group = QGroupBox("Callsign Information")
        callsign_layout = QVBoxLayout(callsign_group)

        self.callsign_info_label = QLabel("<i>Select a spot to view callsign information</i>")
        self.callsign_info_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.callsign_info_label.setWordWrap(True)
        self.callsign_info_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        self.callsign_info_label.setOpenExternalLinks(True)
        self.callsign_info_label.setStyleSheet("padding: 10px; font-family: monospace;")
        callsign_layout.addWidget(self.callsign_info_label)

        # QSL card image label
        self.qsl_card_label = QLabel()
        self.qsl_card_label.setAlignment(Qt.AlignCenter)
        self.qsl_card_label.setScaledContents(False)
        self.qsl_card_label.setStyleSheet("padding: 10px;")
        self.qsl_card_label.hide()  # Hidden by default
        callsign_layout.addWidget(self.qsl_card_label)

        details_layout.addWidget(callsign_group)
        details_layout.addStretch()

        main_splitter.addWidget(details_widget)

        # Set initial splitter sizes (70% table, 30% details)
        main_splitter.setSizes([700, 300])

        layout.addWidget(main_splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def create_menus(self):
        """Create application menus"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        logbook_action = QAction("View &Logbook", self)
        logbook_action.triggered.connect(self.open_logbook)
        file_menu.addAction(logbook_action)

        file_menu.addSeparator()

        export_action = QAction("&Export Log (ADIF)", self)
        export_action.triggered.connect(self.export_log)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        upload_action = QAction("&Upload to QRZ Logbook", self)
        upload_action.triggered.connect(self.upload_log)
        tools_menu.addAction(upload_action)

        settings_action = QAction("&Settings", self)
        settings_action.triggered.connect(self.open_settings)
        tools_menu.addAction(settings_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_refresh_timer(self):
        """Setup automatic refresh timer"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_spots)
        self.refresh_timer.start(60000)  # Refresh every 60 seconds

    def refresh_spots(self):
        """Refresh POTA spots from API"""
        self.status_bar.showMessage("Refreshing spots...")
        try:
            spots = self.pota_service.get_spots()
            self.all_spots = spots  # Store all spots for filtering
            self.apply_filters()  # Apply current filters
            self.status_bar.showMessage(f"Loaded {len(spots)} spots", 5000)
        except Exception as e:
            self.status_bar.showMessage(f"Error: {str(e)}", 5000)

    def populate_spots_table(self, spots):
        """Populate the spots table with data and apply color coding"""
        self.spots_table.setSortingEnabled(False)
        self.spots_table.setRowCount(len(spots))

        for row, spot in enumerate(spots):
            mode = spot.get('mode', '').upper()

            # Create items
            time_item = QTableWidgetItem(spot.get('spotTime', ''))
            callsign_item = QTableWidgetItem(spot.get('activator', ''))
            freq_item = QTableWidgetItem(spot.get('frequency', ''))
            mode_item = QTableWidgetItem(spot.get('mode', ''))
            park_item = QTableWidgetItem(spot.get('reference', ''))
            location_item = QTableWidgetItem(spot.get('locationDesc', ''))
            spotter_item = QTableWidgetItem(spot.get('spotter', ''))

            # Apply color coding based on mode
            color = self.get_mode_color(mode)
            if color:
                brush = QBrush(color)
                time_item.setBackground(brush)
                callsign_item.setBackground(brush)
                freq_item.setBackground(brush)
                mode_item.setBackground(brush)
                park_item.setBackground(brush)
                location_item.setBackground(brush)
                spotter_item.setBackground(brush)

            # Set items in table
            self.spots_table.setItem(row, 0, time_item)
            self.spots_table.setItem(row, 1, callsign_item)
            self.spots_table.setItem(row, 2, freq_item)
            self.spots_table.setItem(row, 3, mode_item)
            self.spots_table.setItem(row, 4, park_item)
            self.spots_table.setItem(row, 5, location_item)
            self.spots_table.setItem(row, 6, spotter_item)

        self.spots_table.setSortingEnabled(True)

    def get_mode_color(self, mode: str) -> QColor:
        """
        Get color for a given mode

        Args:
            mode: Mode string (e.g., 'CW', 'SSB', 'FT8')

        Returns:
            QColor object or None
        """
        mode_upper = mode.upper()

        # Direct match
        if mode_upper in self.MODE_COLORS:
            return self.MODE_COLORS[mode_upper]

        # Category matching
        digital_modes = ['FT8', 'FT4', 'RTTY', 'PSK31', 'PSK63', 'JS8', 'MFSK', 'OLIVIA']
        phone_modes = ['SSB', 'USB', 'LSB', 'FM', 'AM']

        for digital in digital_modes:
            if digital in mode_upper:
                return self.MODE_COLORS.get('FT8')  # Use green for all digital

        for phone in phone_modes:
            if phone in mode_upper:
                return self.MODE_COLORS.get('SSB')  # Use navajo white for all phone

        if 'CW' in mode_upper:
            return self.MODE_COLORS.get('CW')

        return None  # No color for unknown modes

    def toggle_auto_refresh(self):
        """Toggle automatic refresh on/off"""
        if self.auto_refresh_button.isChecked():
            self.refresh_timer.start(60000)
            self.auto_refresh_button.setText("Auto-Refresh: ON")
        else:
            self.refresh_timer.stop()
            self.auto_refresh_button.setText("Auto-Refresh: OFF")

    def handle_table_double_click(self, index):
        """
        Handle double-click on table based on column
        - Column 1 (Callsign): Open logging dialog
        - Column 4 (Park): Open park page in browser
        - Other columns: Open logging dialog
        """
        column = index.column()
        row = index.row()

        if column == 4:  # Park column
            self.open_park_page(row)
        else:  # Any other column - open logging dialog
            self.open_logging_dialog_from_row(row)

    def open_park_page(self, row):
        """
        Open the POTA park page in the default browser

        Args:
            row: Table row number
        """
        if row < 0:
            return

        park_reference = self.spots_table.item(row, 4).text()
        if park_reference:
            url = f"https://pota.app/#/park/{park_reference}"
            QDesktopServices.openUrl(QUrl(url))
            self.status_bar.showMessage(f"Opening park {park_reference} in browser...", 3000)

    def open_logging_dialog(self):
        """Open logging dialog with selected spot data"""
        current_row = self.spots_table.currentRow()
        if current_row < 0:
            return
        self.open_logging_dialog_from_row(current_row)

    def open_logging_dialog_from_row(self, row):
        """
        Open logging dialog for a specific row

        Args:
            row: Table row number
        """
        if row < 0:
            return

        # Extract spot data from table
        spot_data = {
            'callsign': self.spots_table.item(row, 1).text(),
            'frequency': self.spots_table.item(row, 2).text(),
            'mode': self.spots_table.item(row, 3).text(),
            'park': self.spots_table.item(row, 4).text(),
            'location': self.spots_table.item(row, 5).text(),
        }

        # Add name from QRZ lookup if available
        callsign = spot_data['callsign']
        if self.current_qrz_info and self.current_qrz_info.get('callsign', '').upper() == callsign.upper():
            # Get first name and last name from QRZ info
            first_name = self.current_qrz_info.get('first_name', '')
            last_name = self.current_qrz_info.get('last_name', '')
            if first_name or last_name:
                spot_data['name'] = f"{first_name} {last_name}".strip()

        dialog = LoggingDialog(spot_data, self, self.cat_service)
        if dialog.exec():
            # Refresh logbook after saving a QSO
            self.refresh_logbook()

    def export_log(self):
        """Export log to ADIF file"""
        # Get all QSOs from database
        db_manager = DatabaseManager()
        qsos = db_manager.get_all_qsos()

        if not qsos:
            QMessageBox.information(
                self,
                "No QSOs",
                "There are no QSOs in your logbook to export.\n\n"
                "Log some contacts first, then try exporting again."
            )
            return

        # Generate default filename with current date
        from datetime import datetime
        default_filename = f"potahunter_log_{datetime.now().strftime('%Y%m%d')}.adi"

        # Open file dialog
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Log to ADIF",
            default_filename,
            "ADIF Files (*.adi *.adif);;All Files (*)"
        )

        if not filename:
            # User cancelled
            return

        # Ensure proper extension
        filename = ADIFExporter.validate_adif_filename(filename)

        # Export to file
        self.status_bar.showMessage("Exporting log...", 0)
        try:
            success = ADIFExporter.export_to_file(qsos, filename)

            if success:
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Successfully exported {len(qsos)} QSO(s) to:\n\n{filename}\n\n"
                    f"You can now import this file into other logging software "
                    f"or upload it to QRZ Logbook or LoTW."
                )
                self.status_bar.showMessage(f"Exported {len(qsos)} QSOs to {filename}", 5000)
            else:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"Failed to export log to {filename}.\n\n"
                    f"Please check the file path and permissions."
                )
                self.status_bar.showMessage("Export failed", 5000)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"An error occurred while exporting:\n\n{str(e)}"
            )
            self.status_bar.showMessage("Export failed", 5000)

    def upload_log(self):
        """Upload log to QRZ Logbook"""
        from PySide6.QtWidgets import QMessageBox
        from potahunter.ui.qrz_upload_dialog import QRZUploadDialog
        from potahunter.models.database import DatabaseManager

        # Check if API key is configured
        api_key = self.settings.value("qrz/api_key", "")
        if not api_key:
            reply = QMessageBox.question(
                self,
                "QRZ API Key Required",
                "You need to configure your QRZ Logbook API key before uploading.\n\n"
                "Would you like to open the settings dialog now?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.open_settings()
            return

        # Get all QSOs from database
        db_manager = DatabaseManager()
        qsos = db_manager.get_all_qsos()

        if not qsos:
            QMessageBox.information(
                self,
                "No QSOs",
                "There are no QSOs in your logbook to upload.\n\n"
                "Log some contacts first, then try uploading again."
            )
            return

        # Open upload dialog
        dialog = QRZUploadDialog(qsos, api_key, self)
        if dialog.exec():
            self.status_bar.showMessage("Upload completed", 3000)

    def refresh_logbook(self):
        """Refresh logbook from database"""
        try:
            # Get all QSOs from database
            self.all_qsos = self.db_manager.get_all_qsos()

            # Apply current filter
            self.filter_logbook()

            self.status_bar.showMessage(f"Loaded {len(self.all_qsos)} QSOs", 2000)
        except Exception as e:
            self.status_bar.showMessage(f"Error loading logbook: {str(e)}", 5000)
            logging.error(f"Error refreshing logbook: {e}")

    def filter_logbook(self, filter_text="", filter_type=""):
        """Filter and populate logbook table

        Args:
            filter_text: Text to filter by (callsign or park)
            filter_type: Type of filter ('Callsign', 'Park', or empty for no filter)
        """
        try:
            # Filter QSOs based on filter type
            if filter_type == "Callsign" and filter_text:
                filtered_qsos = [qso for qso in self.all_qsos if qso.callsign.upper() == filter_text.upper()]
            elif filter_type == "Park" and filter_text:
                filtered_qsos = [qso for qso in self.all_qsos if qso.park_reference and qso.park_reference.upper() == filter_text.upper()]
            else:
                filtered_qsos = self.all_qsos

            # Update table
            self.populate_logbook_table(filtered_qsos)

            # Update count label
            if filtered_qsos != self.all_qsos:
                self.logbook_count_label.setText(f"{len(filtered_qsos)} of {len(self.all_qsos)} QSOs")
            else:
                self.logbook_count_label.setText(f"{len(self.all_qsos)} QSOs")

        except Exception as e:
            logging.error(f"Error filtering logbook: {e}")

    def populate_logbook_table(self, qsos):
        """Populate logbook table with QSO data"""
        self.logbook_table.setSortingEnabled(False)
        self.logbook_table.setRowCount(len(qsos))

        for row, qso in enumerate(qsos):
            # Format date (YYYYMMDD -> YYYY-MM-DD)
            date_str = qso.qso_date
            if len(date_str) == 8:
                formatted_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
            else:
                formatted_date = date_str

            # Format time (HHMMSS -> HH:MM:SS or HHMM -> HH:MM)
            time_str = qso.time_on
            if len(time_str) == 6:
                formatted_time = f"{time_str[0:2]}:{time_str[2:4]}:{time_str[4:6]}"
            elif len(time_str) == 4:
                formatted_time = f"{time_str[0:2]}:{time_str[2:4]}"
            else:
                formatted_time = time_str

            # Populate row
            self.logbook_table.setItem(row, 0, QTableWidgetItem(formatted_date))
            self.logbook_table.setItem(row, 1, QTableWidgetItem(formatted_time))
            self.logbook_table.setItem(row, 2, QTableWidgetItem(qso.callsign or ""))
            self.logbook_table.setItem(row, 3, QTableWidgetItem(qso.frequency or ""))
            self.logbook_table.setItem(row, 4, QTableWidgetItem(qso.mode or ""))
            self.logbook_table.setItem(row, 5, QTableWidgetItem(qso.band or ""))
            self.logbook_table.setItem(row, 6, QTableWidgetItem(qso.rst_sent or ""))
            self.logbook_table.setItem(row, 7, QTableWidgetItem(qso.rst_rcvd or ""))
            self.logbook_table.setItem(row, 8, QTableWidgetItem(qso.park_reference or ""))
            self.logbook_table.setItem(row, 9, QTableWidgetItem(qso.name or ""))
            self.logbook_table.setItem(row, 10, QTableWidgetItem(qso.qth or ""))
            self.logbook_table.setItem(row, 11, QTableWidgetItem(qso.state or ""))
            self.logbook_table.setItem(row, 12, QTableWidgetItem(qso.comment or ""))

        self.logbook_table.setSortingEnabled(True)

    def on_logbook_filter_changed(self):
        """Handle logbook filter dropdown change"""
        filter_mode = self.logbook_filter_combo.currentText()

        # If filter mode is "None", show all QSOs
        if filter_mode == "None":
            self.filter_logbook()
        else:
            # If there's a selected spot, apply the filter immediately
            current_row = self.spots_table.currentRow()
            if current_row >= 0:
                self.apply_logbook_filter_for_current_spot()

    def apply_logbook_filter_for_current_spot(self):
        """Apply logbook filter based on currently selected POTA spot"""
        filter_mode = self.logbook_filter_combo.currentText()

        if filter_mode == "None":
            self.filter_logbook()
            return

        current_row = self.spots_table.currentRow()
        if current_row < 0:
            return

        # Get the callsign and park from the selected spot
        callsign_item = self.spots_table.item(current_row, 1)  # Callsign column
        park_item = self.spots_table.item(current_row, 4)  # Park column

        if filter_mode == "Callsign" and callsign_item:
            filter_text = callsign_item.text()
            self.filter_logbook(filter_text, "Callsign")
        elif filter_mode == "Park" and park_item:
            filter_text = park_item.text()
            self.filter_logbook(filter_text, "Park")

    def open_logbook(self):
        """Open logbook viewer window"""
        logbook_window = LogbookViewer(self)
        logbook_window.logbook_modified.connect(self.refresh_logbook)  # Refresh when logbook is modified
        logbook_window.show()
        self.status_bar.showMessage("Opened logbook viewer", 2000)

    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self)

        # Load current QRZ credentials
        username = self.settings.value("qrz/username", "")
        password = self.settings.value("qrz/password", "")
        api_key = self.settings.value("qrz/api_key", "")
        auto_upload = self.settings.value("qrz/auto_upload", False, type=bool)
        dialog.set_qrz_credentials(username, password)
        dialog.set_qrz_api_key(api_key)
        dialog.set_auto_upload_enabled(auto_upload)

        # Load current station information
        station_info = {
            'my_callsign': self.settings.value("station/my_callsign", ""),
            'operator': self.settings.value("station/operator", ""),
            'my_gridsquare': self.settings.value("station/my_gridsquare", ""),
            'my_street': self.settings.value("station/my_street", ""),
            'my_city': self.settings.value("station/my_city", ""),
            'my_county': self.settings.value("station/my_county", ""),
            'my_state': self.settings.value("station/my_state", ""),
            'my_postal_code': self.settings.value("station/my_postal_code", ""),
            'my_country': self.settings.value("station/my_country", ""),
            'my_dxcc': self.settings.value("station/my_dxcc", ""),
            'my_lat': self.settings.value("station/my_lat", ""),
            'my_lon': self.settings.value("station/my_lon", ""),
            'my_rig': self.settings.value("station/my_rig", ""),
            'tx_pwr': self.settings.value("station/tx_pwr", ""),
            'ant_az': self.settings.value("station/ant_az", ""),
        }
        dialog.set_station_info(station_info)

        # Load current CAT settings
        cat_settings = {
            'cat_enabled': self.settings.value("cat/enabled", False, type=bool),
            'cat_radio_model': self.settings.value("cat/radio_model", ""),
            'cat_com_port': self.settings.value("cat/com_port", ""),
            'cat_baud_rate': self.settings.value("cat/baud_rate", None, type=int),
        }
        dialog.set_cat_settings(cat_settings)

        if dialog.exec():
            # Save QRZ credentials
            username, password = dialog.get_qrz_credentials()
            api_key = dialog.get_qrz_api_key()
            auto_upload = dialog.get_auto_upload_enabled()
            self.settings.setValue("qrz/username", username)
            self.settings.setValue("qrz/password", password)
            self.settings.setValue("qrz/api_key", api_key)
            self.settings.setValue("qrz/auto_upload", auto_upload)

            # Save station information
            station_info = dialog.get_station_info()
            for key, value in station_info.items():
                self.settings.setValue(f"station/{key}", value)

            # Save CAT settings
            cat_settings = dialog.get_cat_settings()
            old_enabled = self.settings.value("cat/enabled", False, type=bool)
            for key, value in cat_settings.items():
                # Convert cat_enabled to cat/enabled format
                settings_key = f"cat/{key.replace('cat_', '')}"
                if value is None:
                    self.settings.remove(settings_key)
                else:
                    self.settings.setValue(settings_key, value)

            # Update QRZ service
            self.qrz_service.set_credentials(username, password)

            # Update CAT service
            new_enabled = cat_settings.get('cat_enabled', False)
            if old_enabled and not new_enabled:
                # Disconnect if disabled
                self.cat_service.disconnect()
            elif new_enabled:
                # Disconnect and reconnect with new settings
                self.cat_service.disconnect()
                radio_model = cat_settings.get('cat_radio_model', '')
                com_port = cat_settings.get('cat_com_port', '')
                baud_rate = cat_settings.get('cat_baud_rate')

                if radio_model and com_port:
                    if self.cat_service.connect(com_port, radio_model, baud_rate):
                        self.status_bar.showMessage(f"Connected to {radio_model} on {com_port}", 5000)
                    else:
                        self.status_bar.showMessage(f"Failed to connect to radio on {com_port}", 5000)

            self.status_bar.showMessage("Settings saved", 3000)

    def show_about(self):
        """Show about dialog"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(
            self,
            "About POTA Hunter",
            "POTA Hunter v0.1.0\n\n"
            "A Parks on the Air spotting and logging application.\n\n"
            "Built with PySide6"
        )

    def apply_filters(self):
        """Apply current filter settings to the spots table"""
        filtered_spots = self.filter_spots(self.all_spots)
        self.populate_spots_table(filtered_spots)

        # Update status bar
        if len(filtered_spots) < len(self.all_spots):
            self.status_bar.showMessage(
                f"Showing {len(filtered_spots)} of {len(self.all_spots)} spots",
                3000
            )

    def filter_spots(self, spots):
        """
        Filter spots based on current filter settings

        Args:
            spots: List of spot dictionaries

        Returns:
            Filtered list of spots
        """
        if not spots:
            return []

        filtered = spots

        # Band filter
        band_selection = self.band_filter.currentText()
        if band_selection != "All Bands":
            filtered = [s for s in filtered if self.spot_matches_band(s, band_selection)]

        # Mode filter
        mode_selection = self.mode_filter.currentText()
        if mode_selection != "All Modes":
            filtered = [s for s in filtered if self.spot_matches_mode(s, mode_selection)]

        # Search filter (park or callsign)
        search_text = self.search_filter.currentText().strip().upper()
        if search_text:
            filtered = [s for s in filtered if self.spot_matches_search(s, search_text)]

        return filtered

    def spot_matches_band(self, spot, band: str) -> bool:
        """
        Check if spot matches the selected band

        Args:
            spot: Spot dictionary
            band: Band string (e.g., "20m")

        Returns:
            True if matches, False otherwise
        """
        try:
            freq = float(spot.get('frequency', '0')) / 1000
        except (ValueError, TypeError):
            return False

        # Map bands to frequency ranges (in MHz)
        band_ranges = {
            '160m': (1.8, 2.0),
            '80m': (3.5, 4.0),
            '60m': (5.3, 5.4),
            '40m': (7.0, 7.3),
            '30m': (10.1, 10.15),
            '20m': (14.0, 14.35),
            '17m': (18.068, 18.168),
            '15m': (21.0, 21.45),
            '12m': (24.89, 24.99),
            '10m': (28.0, 29.7),
            '6m': (50.0, 54.0),
            '2m': (144.0, 148.0),
        }

        if band in band_ranges:
            low, high = band_ranges[band]
            return low <= freq < high

        return False

    def spot_matches_mode(self, spot, mode_category: str) -> bool:
        """
        Check if spot matches the selected mode category

        Args:
            spot: Spot dictionary
            mode_category: Mode category ("CW", "Digital", "Phone")

        Returns:
            True if matches, False otherwise
        """
        mode = spot.get('mode', '').upper()

        if mode_category == "CW":
            return 'CW' in mode

        elif mode_category == "Digital":
            digital_modes = ['FT8', 'FT4', 'RTTY', 'PSK', 'JS8', 'MFSK', 'OLIVIA', 'CONTESTIA']
            return any(digital in mode for digital in digital_modes)

        elif mode_category == "Phone":
            phone_modes = ['SSB', 'USB', 'LSB', 'FM', 'AM']
            return any(phone in mode for phone in phone_modes)

        return False

    def spot_matches_search(self, spot, search_text: str) -> bool:
        """
        Check if spot matches the search text (park or callsign)

        Args:
            spot: Spot dictionary
            search_text: Search string

        Returns:
            True if matches, False otherwise
        """
        park = spot.get('reference', '').upper()
        callsign = spot.get('activator', '').upper()
        location = spot.get('locationDesc', '').upper()

        return (search_text in park or
                search_text in callsign or
                search_text in location)

    def clear_filters(self):
        """Clear all filter settings"""
        self.band_filter.setCurrentIndex(0)  # "All Bands"
        self.mode_filter.setCurrentIndex(0)  # "All Modes"
        self.search_filter.clearEditText()
        self.apply_filters()

    def load_qrz_credentials(self):
        """Load QRZ credentials from settings"""
        username = self.settings.value("qrz/username", "")
        password = self.settings.value("qrz/password", "")

        if username and password:
            self.qrz_service.set_credentials(username, password)

    def load_cat_settings(self):
        """Load CAT settings from settings and connect if enabled"""
        cat_enabled = self.settings.value("cat/enabled", False, type=bool)
        radio_model = self.settings.value("cat/radio_model", "")
        com_port = self.settings.value("cat/com_port", "")
        baud_rate = self.settings.value("cat/baud_rate", None, type=int)

        if cat_enabled and radio_model and com_port:
            if self.cat_service.connect(com_port, radio_model, baud_rate):
                self.status_bar.showMessage(f"Connected to {radio_model} on {com_port}", 5000)
            else:
                self.status_bar.showMessage(f"Failed to connect to radio on {com_port}", 5000)

    def on_cat_frequency_changed(self, frequency):
        """Handle frequency change from CAT"""
        freq_mhz = frequency / 1_000_000
        self.cat_freq_label.setText(f"{freq_mhz:.4f} MHz")

    def on_cat_mode_changed(self, mode):
        """Handle mode change from CAT"""
        # Update display if needed
        pass

    def on_cat_connection_status_changed(self, connected):
        """Handle CAT connection status change"""
        if connected:
            mode = self.cat_service.get_mode()
            self.cat_status_label.setText(f"CAT: Connected, Mode: {mode}")
            self.cat_status_label.setStyleSheet("color: green; padding: 5px; font-weight: bold;")
        else:
            self.cat_status_label.setText("CAT: Disconnected")
            self.cat_status_label.setStyleSheet("color: gray; padding: 5px;")
            self.cat_freq_label.setText("")

    def on_row_selection_changed(self, current, previous):
        """
        Handle row selection change - lookup callsign info from QRZ and tune radio

        Args:
            current: Currently selected item
            previous: Previously selected item
        """
        if not current:
            return

        # Get the row
        row = current.row()
        if row < 0:
            return

        # Tune radio to spot frequency if CAT is connected
        if self.cat_service.is_connected:
            freq_item = self.spots_table.item(row, 2)  # Column 2 is frequency
            if freq_item:
                try:
                    freq_str = freq_item.text().strip()
                    print(f"DEBUG: Raw frequency string from table: '{freq_str}'")

                    # Parse frequency - API returns it in kHz (e.g., "14046" for 14.046 MHz)
                    freq_khz = float(freq_str)
                    print(f"DEBUG: Parsed as kHz: {freq_khz}")

                    # Convert kHz to Hz
                    freq_hz = freq_khz * 1_000
                    freq_mhz = freq_khz / 1_000
                    print(f"DEBUG: Converted to Hz: {freq_hz} ({freq_mhz} MHz)")

                    # Set radio frequency
                    base_mode = self.spots_table.item(row, 3).text().strip()
                    calc_mode = resolve_mode_for_radio(base_mode, freq_mhz)
                    logging.debug(f"Tuning radio to {freq_mhz:.3f} MHz, Mode: {calc_mode}")
                    if self.cat_service.set_frequency(freq_hz):
                        self.status_bar.showMessage(f"Tuned radio to {freq_mhz:.3f} MHz", 2000)
                        print(f"DEBUG: Successfully tuned to {freq_mhz} MHz")
                    else:
                        print(f"DEBUG: Failed to tune to {freq_mhz} MHz")
                    if self.cat_service.set_mode(calc_mode):
                        print(f"DEBUG: Successfully set mode")
                    else:
                        print(f"DEBUG: Failed to set mode")
                except (ValueError, AttributeError) as e:
                    print(f"DEBUG: Error tuning radio: {e}")
                    pass  # Silently ignore tuning errors

        # Get callsign from the table
        callsign_item = self.spots_table.item(row, 1)  # Column 1 is callsign
        if not callsign_item:
            return

        callsign = callsign_item.text().strip()
        if not callsign:
            return

        # Check if QRZ credentials are configured
        if not self.qrz_service.has_credentials():
            self.callsign_info_label.setText(
                "<i>QRZ credentials not configured.<br>"
                "Go to Preferences → QRZ Credentials to add your QRZ credentials.</i>"
            )
            return

        # Show loading message
        self.callsign_info_label.setText(f"<i>Loading information for {callsign}...</i>")
        self.status_bar.showMessage(f"Looking up {callsign} on QRZ...", 2000)

        # Lookup callsign
        info = self.qrz_service.lookup_callsign(callsign)

        if info:
            # Store QRZ info for use in logging dialog
            self.current_qrz_info = info

            # Format and display the information with clickable callsign link
            formatted_info = self.qrz_service.format_callsign_info(info)
            qrz_url = f"https://www.qrz.com/db/{callsign}"
            html_content = f"<b><a href='{qrz_url}'>{callsign}</a></b><br><br>" + formatted_info
            self.callsign_info_label.setText(html_content)

            # Check if there's a QSL card image and download it
            image_url = self.qrz_service.get_image_url(info)
            if image_url:
                self.qsl_card_label.setText("<i>Loading QSL card image...</i>")
                self.qsl_card_label.show()
                request = QNetworkRequest(QUrl(image_url))
                self.network_manager.get(request)
            else:
                self.qsl_card_label.hide()

            self.status_bar.showMessage(f"Loaded info for {callsign}", 2000)
        else:
            # Clear stored QRZ info
            self.current_qrz_info = {}

            qrz_url = f"https://www.qrz.com/db/{callsign}"
            self.callsign_info_label.setText(
                f"<b><a href='{qrz_url}'>{callsign}</a></b><br><br>"
                f"<i>No information found or QRZ lookup failed.<br>"
                f"Check your QRZ credentials and subscription.</i>"
            )
            self.qsl_card_label.hide()
            self.status_bar.showMessage(f"Could not find info for {callsign}", 3000)

        # Apply logbook filter if auto-filter is enabled
        self.apply_logbook_filter_for_current_spot()

    def on_image_downloaded(self, reply: QNetworkReply):
        """
        Handle downloaded QSL card image

        Args:
            reply: Network reply containing image data
        """
        if reply.error() == QNetworkReply.NetworkError.NoError:
            image_data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)

            if not pixmap.isNull():
                # Scale image to fit in the panel (max width 300px, maintain aspect ratio)
                scaled_pixmap = pixmap.scaledToWidth(300, Qt.TransformationMode.SmoothTransformation)
                self.qsl_card_label.setPixmap(scaled_pixmap)
                self.qsl_card_label.setText("")
            else:
                self.qsl_card_label.setText("<i>Failed to load image</i>")
        else:
            self.qsl_card_label.setText(f"<i>Error loading image: {reply.errorString()}</i>")

        reply.deleteLater()
