"""
Main window for POTA Hunter application
"""

import logging
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QStatusBar, QMenuBar, QMenu, QComboBox, QLabel, QCheckBox,
    QTextEdit, QGroupBox, QSplitter, QSizePolicy, QScrollArea, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QUrl, QSettings, QByteArray, QThread, Signal, QCoreApplication
from PySide6.QtGui import QAction, QColor, QBrush, QDesktopServices, QPixmap, QIcon
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import os

from potahunter.services.pota_api import PotaAPIService
from potahunter.services.qrz_api import QRZAPIService
from potahunter.services.cat_service import CATService
from potahunter.ui.logging_dialog import LoggingDialog, resolve_mode_for_radio
from potahunter.ui.settings_dialog import SettingsDialog
from potahunter.ui.logbook_viewer import LogbookViewer
from potahunter.models.database import DatabaseManager
from potahunter.models.qso import QSO
from potahunter.utils.adif_export import ADIFExporter
from potahunter.utils.adif_import import ADIFImporter
from potahunter.version import __version__, APP_NAME


class TimeTableWidgetItem(QTableWidgetItem):
    """Custom QTableWidgetItem that sorts by stored timestamp instead of displayed text"""

    def __lt__(self, other):
        """Compare based on stored timestamp data rather than displayed text"""
        # Get the stored timestamp from UserRole
        self_time = self.data(Qt.UserRole)
        other_time = other.data(Qt.UserRole)

        # If both have timestamps, compare them
        if self_time and other_time:
            return self_time < other_time

        # Fall back to text comparison if timestamps are missing
        return super().__lt__(other)


class QRZLookupWorker(QThread):
    """Worker thread for QRZ callsign lookups"""

    finished = Signal(object)  # Emits the QRZ info dict or None

    def __init__(self, qrz_service, callsign):
        super().__init__()
        self.qrz_service = qrz_service
        self.callsign = callsign

    def run(self):
        """Perform the QRZ lookup in background thread"""
        import time
        try:
            start_time = time.time()
            info = self.qrz_service.lookup_callsign(self.callsign)

            # Ensure minimum display time of 300ms for loading indicator
            elapsed = time.time() - start_time
            if elapsed < 0.3:
                time.sleep(0.3 - elapsed)

            self.finished.emit(info)
        except Exception as e:
            logging.error(f"Error in QRZ lookup thread: {e}")
            self.finished.emit(None)


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

        # Set application icon
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

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
        self.qrz_lookup_worker = None  # Worker thread for QRZ lookups
        self.current_lookup_callsign = ""  # Track which callsign is being looked up
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

        # Load logbook visibility state
        self.load_logbook_visibility()

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

        # Mode filter with checkboxes
        filter_layout.addWidget(QLabel("Mode:"))
        mode_filter_widget = QWidget()
        mode_filter_layout = QHBoxLayout(mode_filter_widget)
        mode_filter_layout.setContentsMargins(0, 0, 0, 0)
        mode_filter_layout.setSpacing(10)

        self.mode_filter_cw = QCheckBox("CW")
        self.mode_filter_cw.setChecked(True)
        self.mode_filter_cw.stateChanged.connect(self.apply_filters)
        mode_filter_layout.addWidget(self.mode_filter_cw)

        self.mode_filter_digital = QCheckBox("Digital")
        self.mode_filter_digital.setChecked(True)
        self.mode_filter_digital.stateChanged.connect(self.apply_filters)
        mode_filter_layout.addWidget(self.mode_filter_digital)

        self.mode_filter_phone = QCheckBox("Phone")
        self.mode_filter_phone.setChecked(True)
        self.mode_filter_phone.stateChanged.connect(self.apply_filters)
        mode_filter_layout.addWidget(self.mode_filter_phone)

        filter_layout.addWidget(mode_filter_widget)

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

        # self.logbook_button = QPushButton("View Logbook")
        # self.logbook_button.clicked.connect(self.open_logbook)
        # button_layout.addWidget(self.logbook_button)

        # self.export_button = QPushButton("Export Log (ADIF)")
        # self.export_button.clicked.connect(self.export_log)
        # button_layout.addWidget(self.export_button)

        # self.upload_button = QPushButton("Upload to QRZ Logbook")
        # self.upload_button.clicked.connect(self.upload_log)
        # button_layout.addWidget(self.upload_button)

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
        self.spots_table.setColumnCount(8)
        self.spots_table.setHorizontalHeaderLabels([
            "Time", "Callsign", "Frequency", "Mode",
            "Park", "Location", "Grid", "Spotter"
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
        self.logbook_widget = QWidget()
        logbook_layout = QVBoxLayout(self.logbook_widget)
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
        self.logbook_table.setColumnCount(14)
        self.logbook_table.setHorizontalHeaderLabels([
            "Date", "Time", "Callsign", "Frequency", "Mode", "Band", "Power",
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

        # Enable row selection highlighting for spots table
        self.spots_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.spots_table.setSelectionMode(QTableWidget.SingleSelection)

        # Ensure selection highlighting is visible with proper styling
        self.spots_table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #0078d7;
                color: white;
            }
            QTableWidget::item:focus {
                background-color: #0078d7;
                color: white;
            }
        """)

        self.logbook_table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #0078d7;
                color: white;
            }
            QTableWidget::item:focus {
                background-color: #0078d7;
                color: white;
            }
        """)

        # Double-click to edit QSO
        self.logbook_table.doubleClicked.connect(self.edit_selected_qso)

        logbook_layout.addWidget(self.logbook_table)

        left_splitter.addWidget(self.logbook_widget)

        # Set initial sizes for vertical splitter (60% POTA spots, 40% logbook)
        left_splitter.setSizes([600, 400])

        main_splitter.addWidget(left_splitter)

        # Details panel on the right
        details_widget = QWidget()
        details_widget.setMinimumWidth(350)  # Set minimum width to prevent shrinking
        details_widget.setMaximumWidth(350)  # Set maximum width to prevent growing
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
        self.qsl_card_label.setMaximumHeight(400)  # Prevent vertical stretching
        self.qsl_card_label.setMaximumWidth(300)   # Constrain width
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

        upload_action = QAction("&Upload to QRZ Logbook", self)
        upload_action.triggered.connect(self.upload_log)
        file_menu.addAction(upload_action)

        file_menu.addSeparator()

        import_action = QAction("&Import ADIF File", self)
        import_action.triggered.connect(self.import_adif)
        file_menu.addAction(import_action)

        export_action = QAction("&Export Log (ADIF)", self)
        export_action.triggered.connect(self.export_log)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        

        settings_action = QAction("&Settings", self)
        settings_action.triggered.connect(self.open_settings)
        tools_menu.addAction(settings_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        self.show_logbook_action = QAction("Show &Logbook Panel", self)
        self.show_logbook_action.setCheckable(True)
        self.show_logbook_action.setChecked(True)  # Default to visible
        self.show_logbook_action.triggered.connect(self.toggle_logbook_visibility)
        view_menu.addAction(self.show_logbook_action)

        self.show_logbook_view = QAction("&View Logbook", self)
        self.show_logbook_view.triggered.connect(self.open_logbook)
        view_menu.addAction(self.show_logbook_view)
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

    def calculate_minutes_ago(self, spot_time_str: str) -> str:
        """
        Calculate how many minutes ago a spot was posted

        Args:
            spot_time_str: Spot time string (ISO format)

        Returns:
            String like "1 min ago", "10 min ago", etc.
        """
        try:
            from datetime import datetime, timezone
            # Parse ISO format timestamp (e.g., "2025-01-19T12:34:56")
            spot_time = datetime.fromisoformat(spot_time_str.replace('Z', '+00:00'))

            # If spot_time is naive (no timezone), assume it's UTC
            if spot_time.tzinfo is None:
                spot_time = spot_time.replace(tzinfo=timezone.utc)

            # Get current time in UTC
            now = datetime.now(timezone.utc)

            # Calculate difference in minutes
            time_diff = now - spot_time
            minutes = max(1, int(time_diff.total_seconds() / 60))

            return f"{minutes} min ago"
        except (ValueError, AttributeError, TypeError):
            # If parsing fails, return the original string
            return spot_time_str

    def populate_spots_table(self, spots):
        """Populate the spots table with data and apply color coding"""
        # Save currently selected spot to restore after refresh
        selected_callsign = None
        selected_park = None
        current_row = self.spots_table.currentRow()
        if current_row >= 0:
            callsign_item = self.spots_table.item(current_row, 1)
            park_item = self.spots_table.item(current_row, 4)
            if callsign_item and park_item:
                # Strip QSO count if present
                callsign_text = callsign_item.text()
                selected_callsign = callsign_text.split(' (')[0] if ' (' in callsign_text else callsign_text
                # Strip QSO count and park name (after newline) from park if present
                park_text = park_item.text().split('\n')[0]  # Get first line only
                selected_park = park_text.split(' (')[0] if ' (' in park_text else park_text

        self.spots_table.setSortingEnabled(False)
        self.spots_table.setRowCount(len(spots))

        # Get all unique callsigns from spots
        callsigns = [spot.get('activator', '') for spot in spots if spot.get('activator')]

        # Get QSO counts for all callsigns in one efficient query
        qso_counts = self.db_manager.get_callsign_qso_counts(callsigns)

        for row, spot in enumerate(spots):
            mode = spot.get('mode', '').upper()
            callsign = spot.get('activator', '')

            # Create items with relative time using custom item for proper sorting
            spot_time_str = spot.get('spotTime', '')
            relative_time = self.calculate_minutes_ago(spot_time_str)
            time_item = TimeTableWidgetItem(relative_time)
            # Store the original timestamp as user data for sorting
            time_item.setData(Qt.UserRole, spot_time_str)

            # Add QSO count to callsign if > 0
            count = qso_counts.get(callsign.upper(), 0)
            if count > 0:
                callsign_display = f"{callsign} ({count})"
            else:
                callsign_display = callsign
            callsign_item = QTableWidgetItem(callsign_display)

            freq_item = QTableWidgetItem(spot.get('frequency', ''))
            mode_item = QTableWidgetItem(spot.get('mode', ''))

            # Park column with name as second line
            park_count = qso_counts.get(spot.get('reference', '').upper(), 0)
            if park_count > 0:
                park_display = f"{spot.get('reference', '')} ({park_count})"
            else:
                park_display = spot.get('reference', '')

            # Add park name as second line if available
            park_name = spot.get('name', '')
            if park_name:
                park_display += f"\n{park_name}"

            park_item = QTableWidgetItem(park_display)
            location_item = QTableWidgetItem(spot.get('locationDesc', ''))

            # Grid column - prefer grid6, fall back to grid4
            grid_display = spot.get('grid6', '') or spot.get('grid4', '')
            grid_item = QTableWidgetItem(grid_display)

            # Spotter column with comments as second line
            spotter_display = spot.get('spotter', '')
            comments = spot.get('comments', '')
            if comments:
                spotter_display += f"\n{comments}"

            spotter_item = QTableWidgetItem(spotter_display)

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
                grid_item.setBackground(brush)
                spotter_item.setBackground(brush)

            # Set items in table
            self.spots_table.setItem(row, 0, time_item)
            self.spots_table.setItem(row, 1, callsign_item)
            self.spots_table.setItem(row, 2, freq_item)
            self.spots_table.setItem(row, 3, mode_item)
            self.spots_table.setItem(row, 4, park_item)
            self.spots_table.setItem(row, 5, location_item)
            self.spots_table.setItem(row, 6, grid_item)
            self.spots_table.setItem(row, 7, spotter_item)

            # Set row height to accommodate two lines of text
            self.spots_table.setRowHeight(row, 48)

        self.spots_table.setSortingEnabled(True)
        # Sort by Time column (column 0) in descending order to show newest spots first
        self.spots_table.sortItems(0, Qt.DescendingOrder)

        # Restore selection if a spot was previously selected
        if selected_callsign and selected_park:
            # Find the row with matching callsign and park
            for row in range(self.spots_table.rowCount()):
                callsign_item = self.spots_table.item(row, 1)
                park_item = self.spots_table.item(row, 4)
                if callsign_item and park_item:
                    # Strip QSO counts and park name (after newline) for comparison
                    row_callsign = callsign_item.text().split(' (')[0] if ' (' in callsign_item.text() else callsign_item.text()
                    park_text = park_item.text().split('\n')[0]  # Get first line only
                    row_park = park_text.split(' (')[0] if ' (' in park_text else park_text

                    if row_callsign == selected_callsign and row_park == selected_park:
                        # Found the matching spot - select it and scroll to it
                        self.spots_table.selectRow(row)
                        self.spots_table.scrollToItem(self.spots_table.item(row, 0))
                        break

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

        park_text = self.spots_table.item(row, 4).text()
        # Extract park reference (first line, before any count)
        park_reference = park_text.split('\n')[0].split(' (')[0]
        if park_reference:
            url = f"https://pota.app/#/park/{park_reference}"
            self.status_bar.showMessage(f"Opening park {park_reference} in browser...", 3000)
            QDesktopServices.openUrl(QUrl(url))

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
        # Strip QSO count from callsign if present (format: "CALLSIGN (count)")
        callsign_text = self.spots_table.item(row, 1).text()
        if ' (' in callsign_text:
            callsign = callsign_text.split(' (')[0]
        else:
            callsign = callsign_text

        # Extract park reference (first line, before any count)
        park_text = self.spots_table.item(row, 4).text()
        park_reference = park_text.split('\n')[0].split(' (')[0]

        spot_data = {
            'callsign': callsign,
            'frequency': self.spots_table.item(row, 2).text(),
            'mode': self.spots_table.item(row, 3).text(),
            'park': park_reference,
            'location': self.spots_table.item(row, 5).text(),
        }

        # Add name from QRZ lookup - check if we already have it, otherwise do a quick lookup
        callsign = spot_data['callsign']
        qrz_name = None

        # First check if current QRZ info matches this callsign
        if self.current_qrz_info and self.current_qrz_info.get('callsign', '').upper() == callsign.upper():
            first_name = self.current_qrz_info.get('first_name', '')
            last_name = self.current_qrz_info.get('last_name', '')
            if first_name or last_name:
                qrz_name = f"{first_name} {last_name}".strip()

        # If we don't have the name yet and QRZ is configured, do a quick synchronous lookup
        if not qrz_name and self.qrz_service.has_credentials():
            try:
                qrz_info = self.qrz_service.lookup_callsign(callsign)
                if qrz_info:
                    first_name = qrz_info.get('first_name', '')
                    last_name = qrz_info.get('last_name', '')
                    if first_name or last_name:
                        qrz_name = f"{first_name} {last_name}".strip()
            except Exception:
                pass  # Silently ignore QRZ lookup errors

        # Add name to spot data if we got it
        if qrz_name:
            spot_data['name'] = qrz_name

        dialog = LoggingDialog(spot_data, self, self.cat_service)
        if dialog.exec():
            # Refresh logbook after saving a QSO
            self.refresh_logbook()

    def import_adif(self):
        """Import QSOs from an ADIF file"""
        # Open file dialog
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import ADIF File",
            "",
            "ADIF Files (*.adi *.adif);;All Files (*)"
        )

        if not filename:
            # User cancelled
            return

        # Validate file format
        is_valid, error_msg = ADIFImporter.validate_adif_file(filename)
        if not is_valid:
            QMessageBox.critical(
                self,
                "Invalid File",
                f"The selected file does not appear to be a valid ADIF file.\n\n{error_msg}"
            )
            return

        # Import QSOs
        self.status_bar.showMessage("Importing ADIF file...", 0)
        try:
            qsos, errors = ADIFImporter.import_from_file(filename)

            if not qsos and errors:
                QMessageBox.critical(
                    self,
                    "Import Failed",
                    f"Failed to import any QSOs from the file.\n\n"
                    f"Errors:\n" + "\n".join(errors[:5])  # Show first 5 errors
                )
                self.status_bar.showMessage("Import failed", 5000)
                return

            # Add QSOs to database
            db_manager = DatabaseManager()
            imported_count = 0
            skipped_count = 0

            for qso in qsos:
                try:
                    # Mark as uploaded to prevent auto-upload to QRZ
                    qso.qrz_uploaded = True
                    db_manager.add_qso(qso)
                    imported_count += 1
                except Exception as e:
                    skipped_count += 1
                    errors.append(f"Failed to add QSO {qso.callsign}: {str(e)}")

            # Refresh logbook display
            self.refresh_logbook()

            # Show results
            message = f"Successfully imported {imported_count} QSO(s) from:\n\n{filename}"
            if skipped_count > 0:
                message += f"\n\n{skipped_count} QSO(s) were skipped due to errors."
            if errors:
                message += f"\n\nNote: Imported QSOs are marked as 'uploaded' to prevent duplicate uploads to QRZ."
                if len(errors) > 0:
                    message += f"\n\nFirst few errors:\n" + "\n".join(errors[:3])

            QMessageBox.information(
                self,
                "Import Complete",
                message
            )
            self.status_bar.showMessage(f"Imported {imported_count} QSOs", 5000)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"An error occurred while importing:\n\n{str(e)}"
            )
            self.status_bar.showMessage("Import failed", 5000)

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

        # Get unuploaded QSOs from database (for performance)
        db_manager = DatabaseManager()
        qsos = db_manager.get_unuploaded_qsos()

        if not qsos:
            QMessageBox.information(
                self,
                "No QSOs to Upload",
                "There are no unuploaded QSOs in your logbook.\n\n"
                "All QSOs have already been uploaded to QRZ Logbook."
            )
            return

        # Open upload dialog
        dialog = QRZUploadDialog(qsos, api_key, self)
        if dialog.exec():
            self.status_bar.showMessage("Upload completed", 3000)

    def refresh_logbook(self):
        """Refresh logbook from database"""
        try:
            # Get limited QSOs for initial display (most recent 50)
            # Note: When filtering, we'll need to get all QSOs
            self.all_qsos = self.db_manager.get_all_qsos(limit=50)

            # Apply current filter
            self.filter_logbook()

            # Get total count for status message
            stats = self.db_manager.get_stats()
            total_count = stats['total_qsos']

            if len(self.all_qsos) < total_count:
                self.status_bar.showMessage(f"Showing most recent {len(self.all_qsos)} of {total_count} QSOs", 2000)
            else:
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
            # If filtering is active, we need to load all QSOs to search through them
            if (filter_type == "Callsign" and filter_text) or (filter_type == "Park" and filter_text):
                # Load all QSOs for filtering
                all_qsos_full = self.db_manager.get_all_qsos()

                if filter_type == "Callsign":
                    filtered_qsos = [qso for qso in all_qsos_full if qso.callsign.upper() == filter_text.upper()]
                else:  # Park
                    filtered_qsos = [qso for qso in all_qsos_full if qso.park_reference and qso.park_reference.upper() == filter_text.upper()]

                # Update table
                self.populate_logbook_table(filtered_qsos)

                # Get total count
                stats = self.db_manager.get_stats()
                total_count = stats['total_qsos']

                # Update count label
                self.logbook_count_label.setText(f"{len(filtered_qsos)} of {total_count} QSOs")
            else:
                # No filter - show limited recent QSOs
                filtered_qsos = self.all_qsos

                # Update table
                self.populate_logbook_table(filtered_qsos)

                # Get total count for display
                stats = self.db_manager.get_stats()
                total_count = stats['total_qsos']

                # Update count label
                if len(self.all_qsos) < total_count:
                    self.logbook_count_label.setText(f"Showing {len(self.all_qsos)} most recent of {total_count} QSOs")
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
            date_item = QTableWidgetItem(formatted_date)
            time_item = QTableWidgetItem(formatted_time)
            callsign_item = QTableWidgetItem(qso.callsign or "")

            # Store QSO ID in the first column's UserRole for easy retrieval
            date_item.setData(Qt.UserRole, qso.id)

            self.logbook_table.setItem(row, 0, date_item)
            self.logbook_table.setItem(row, 1, time_item)
            self.logbook_table.setItem(row, 2, callsign_item)
            self.logbook_table.setItem(row, 3, QTableWidgetItem(qso.frequency or ""))
            self.logbook_table.setItem(row, 4, QTableWidgetItem(qso.mode or ""))
            self.logbook_table.setItem(row, 5, QTableWidgetItem(qso.band or ""))
            self.logbook_table.setItem(row, 6, QTableWidgetItem(qso.tx_pwr or ""))
            self.logbook_table.setItem(row, 7, QTableWidgetItem(qso.rst_sent or ""))
            self.logbook_table.setItem(row, 8, QTableWidgetItem(qso.rst_rcvd or ""))
            self.logbook_table.setItem(row, 9, QTableWidgetItem(qso.park_reference or ""))
            self.logbook_table.setItem(row, 10, QTableWidgetItem(qso.name or ""))
            self.logbook_table.setItem(row, 11, QTableWidgetItem(qso.qth or ""))
            self.logbook_table.setItem(row, 12, QTableWidgetItem(qso.state or ""))
            self.logbook_table.setItem(row, 13, QTableWidgetItem(qso.comment or ""))

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
            filter_text = callsign_item.text().split('(')[0].strip()
            self.filter_logbook(filter_text, "Callsign")
        elif filter_mode == "Park" and park_item:
            # Extract park reference (first line, before any count)
            park_text = park_item.text().split('\n')[0].split(' (')[0]
            self.filter_logbook(park_text, "Park")

    def open_logbook(self):
        """Open logbook viewer window"""
        logbook_window = LogbookViewer(self)
        logbook_window.logbook_modified.connect(self.refresh_logbook)  # Refresh when logbook is modified
        logbook_window.show()
        self.status_bar.showMessage("Opened logbook viewer", 2000)

    def edit_selected_qso(self):
        """Open edit dialog for selected QSO from logbook table"""
        current_row = self.logbook_table.currentRow()
        if current_row < 0:
            return

        # Get the QSO ID from the table row (stored in UserRole of first column)
        date_item = self.logbook_table.item(current_row, 0)
        if not date_item:
            return

        qso_id = date_item.data(Qt.UserRole)
        if not qso_id:
            return

        # Retrieve the QSO from database by ID
        qso = self.db_manager.get_qso_by_id(qso_id)
        if qso:

            # Create spot_data dict from QSO for the logging dialog
            spot_data = {
                'callsign': qso.callsign,
                'frequency': qso.frequency,
                'mode': qso.mode,
                'park': qso.park_reference or '',
                'name': qso.name or ''
            }

            # Open logging dialog in edit mode
            dialog = LoggingDialog(spot_data, self, self.cat_service)

            # Pre-fill all the fields with existing QSO data
            dialog.callsign_input.setText(qso.callsign or '')
            dialog.frequency_input.setText(qso.frequency or '')
            dialog.date_input.setText(qso.qso_date or '')
            dialog.time_input.setText(qso.time_on or '')
            dialog.rst_sent_input.setText(qso.rst_sent or '59')
            dialog.rst_rcvd_input.setText(qso.rst_rcvd or '59')
            dialog.park_input.setText(qso.park_reference or '')
            dialog.grid_input.setText(qso.gridsquare or '')
            dialog.name_input.setText(qso.name or '')
            dialog.qth_input.setText(qso.qth or '')
            dialog.state_input.setText(qso.state or '')
            dialog.my_grid_input.setText(qso.my_gridsquare or '')
            dialog.comment_input.setPlainText(qso.comment or '')

            # Explicitly update band field from frequency
            dialog.update_band_from_frequency()

            # Set mode in combo box
            mode_index = dialog.mode_combo.findText(qso.mode)
            if mode_index >= 0:
                dialog.mode_combo.setCurrentIndex(mode_index)
            else:
                dialog.mode_combo.setCurrentText(qso.mode or '')

            # Change dialog title to indicate edit mode
            dialog.setWindowTitle(f"Edit QSO - {qso.callsign}")

            # Change button text
            dialog.save_button.setText("Update QSO")

            # Store the QSO ID so we can update instead of insert
            dialog.editing_qso_id = qso.id

            # Connect to custom save method that updates instead of inserts
            dialog.save_button.clicked.disconnect()
            dialog.save_button.clicked.connect(lambda: self.update_qso_from_dialog(dialog, qso.id))

            if dialog.exec():
                self.refresh_logbook()
                self.status_bar.showMessage(f"Updated QSO with {qso.callsign}", 2000)

    def update_qso_from_dialog(self, dialog, qso_id):
        """Update an existing QSO from the logging dialog"""
        # Validate required fields
        if not dialog.callsign_input.text().strip():
            QMessageBox.warning(dialog, "Invalid Input", "Callsign is required")
            return

        if not dialog.frequency_input.text().strip():
            QMessageBox.warning(dialog, "Invalid Input", "Frequency is required")
            return

        if not dialog.mode_combo.currentText().strip():
            QMessageBox.warning(dialog, "Invalid Input", "Mode is required")
            return

        try:
            # Load station information from settings
            my_callsign = self.settings.value("station/my_callsign", None)
            operator = self.settings.value("station/operator", None)
            my_gridsquare = dialog.my_grid_input.text().strip().upper() or self.settings.value("station/my_gridsquare", None)
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
            ant_az = self.settings.value("station/ant_az", None)

            # Get mode-specific power level from CAT settings
            mode = dialog.mode_combo.currentText().strip().upper()
            tx_pwr = dialog.get_power_for_mode(mode)

            # Create updated QSO object
            qso = QSO(
                id=qso_id,
                callsign=dialog.callsign_input.text().strip().upper(),
                frequency=dialog.frequency_input.text().strip(),
                mode=mode,
                qso_date=dialog.date_input.text().strip(),
                time_on=dialog.time_input.text().strip(),
                rst_sent=dialog.rst_sent_input.text().strip(),
                rst_rcvd=dialog.rst_rcvd_input.text().strip(),
                park_reference=dialog.park_input.text().strip().upper() or None,
                gridsquare=dialog.grid_input.text().strip().upper() or None,
                name=dialog.name_input.text().strip() or None,
                qth=dialog.qth_input.text().strip() or None,
                state=dialog.state_input.text().strip().upper() or None,
                comment=dialog.comment_input.toPlainText().strip() or None,
                band=self._calculate_band_from_frequency(dialog.frequency_input.text().strip()),
                sig="POTA" if dialog.park_input.text().strip() else None,
                sig_info=dialog.park_input.text().strip().upper() or None,
                # My station information
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

            # Update in database
            self.db_manager.update_qso(qso)

            QMessageBox.information(
                dialog,
                "QSO Updated",
                f"Contact with {qso.callsign} updated successfully!"
            )

            dialog.accept()

        except Exception as e:
            QMessageBox.critical(
                dialog,
                "Error",
                f"Failed to update QSO: {str(e)}"
            )

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
            'cat_power_ssb': self.settings.value("cat/power_ssb", None, type=int),
            'cat_power_data': self.settings.value("cat/power_data", None, type=int),
            'cat_power_cw': self.settings.value("cat/power_cw", None, type=int),
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
            f"About {APP_NAME}",
            f"{APP_NAME} v{__version__}\n\n"
            "A Parks on the Air spotting and logging application.\n\n"
            "Built by JK Labs (https://johnkochjr.com)\n"
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

        # Mode filter - check which mode categories are selected
        selected_modes = []
        if self.mode_filter_cw.isChecked():
            selected_modes.append("CW")
        if self.mode_filter_digital.isChecked():
            selected_modes.append("Digital")
        if self.mode_filter_phone.isChecked():
            selected_modes.append("Phone")

        # Only filter if at least one mode is unchecked (not all selected)
        if len(selected_modes) < 3:
            filtered = [s for s in filtered if any(self.spot_matches_mode(s, mode) for mode in selected_modes)]

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
        # Check all mode filters
        self.mode_filter_cw.setChecked(True)
        self.mode_filter_digital.setChecked(True)
        self.mode_filter_phone.setChecked(True)
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

                    # Parse frequency - API returns it in kHz (e.g., "14046" for 14.046 MHz)
                    freq_khz = float(freq_str)

                    # Convert kHz to Hz
                    freq_hz = freq_khz * 1_000
                    freq_mhz = freq_khz / 1_000

                    # Set radio frequency
                    base_mode = self.spots_table.item(row, 3).text().strip()
                    calc_mode = resolve_mode_for_radio(base_mode, freq_mhz)
                    logging.debug(f"Tuning radio to {freq_mhz:.3f} MHz, Mode: {calc_mode}")

                    # Set mode first
                    if self.cat_service.set_mode(calc_mode):

                        # After setting mode, adjust power if configured
                        power = self._get_power_for_mode(calc_mode)
                        if power is not None:
                            if self.cat_service.set_power(power):
                                logging.debug(f"Set power to {power}W for mode {calc_mode}")
                            else:
                                logging.warning(f"Failed to set power to {power}W")
                    else:
                        self.status_bar.showMessage(f"Failed to set mode to {calc_mode}", 5000)

                    # Set frequency
                    if self.cat_service.set_frequency(freq_hz):
                        self.status_bar.showMessage(f"Tuned radio to {freq_mhz:.3f} MHz", 2000)
                    else:
                        self.status_bar.showMessage(f"Failed to tune radio to {freq_mhz:.3f} MHz", 5000)
                except (ValueError, AttributeError) as e:
                    pass  # Silently ignore tuning errors

        # Get callsign from the table
        callsign_item = self.spots_table.item(row, 1)  # Column 1 is callsign
        if not callsign_item:
            return

        # Strip QSO count from callsign if present (format: "CALLSIGN (count)")
        callsign_text = callsign_item.text().strip()
        if ' (' in callsign_text:
            callsign = callsign_text.split(' (')[0]
        else:
            callsign = callsign_text

        if not callsign:
            return

        # Check if QRZ credentials are configured
        if not self.qrz_service.has_credentials():
            self.callsign_info_label.setText(
                "<i>QRZ credentials not configured.<br>"
                "Go to Preferences → QRZ Credentials to add your QRZ credentials.</i>"
            )
            return

        # Show loading message with spinner-like effect
        self.callsign_info_label.setText(
            f"<div style='text-align: center; padding: 20px;'>"
            f"<b style='font-size: 16px;'>{callsign}</b><br><br>"
            f"<i style='color: #666;'>Loading callsign information...</i><br>"
            f"<span style='font-size: 24px;'>⏳</span>"
            f"</div>"
        )
        self.qsl_card_label.hide()
        self.status_bar.showMessage(f"Looking up {callsign} on QRZ...", 0)

        # Force UI to update and show the loading indicator
        QCoreApplication.processEvents()

        # Cancel any existing lookup
        if self.qrz_lookup_worker and self.qrz_lookup_worker.isRunning():
            self.qrz_lookup_worker.finished.disconnect()
            self.qrz_lookup_worker.quit()
            self.qrz_lookup_worker.wait()

        # Start lookup in background thread
        self.current_lookup_callsign = callsign
        self.qrz_lookup_worker = QRZLookupWorker(self.qrz_service, callsign)
        self.qrz_lookup_worker.finished.connect(self.on_qrz_lookup_finished)
        self.qrz_lookup_worker.start()

    def on_qrz_lookup_finished(self, info):
        """
        Handle QRZ lookup completion from background thread

        Args:
            info: QRZ info dict or None
        """
        callsign = self.current_lookup_callsign

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

    def toggle_logbook_visibility(self):
        """Toggle the logbook panel visibility"""
        is_visible = self.show_logbook_action.isChecked()
        self.logbook_widget.setVisible(is_visible)

        # Save the state to settings
        self.settings.setValue("view/logbook_visible", is_visible)

        # Update status bar
        if is_visible:
            self.status_bar.showMessage("Logbook panel shown", 2000)
        else:
            self.status_bar.showMessage("Logbook panel hidden", 2000)

    def load_logbook_visibility(self):
        """Load logbook visibility state from settings"""
        is_visible = self.settings.value("view/logbook_visible", True, type=bool)
        self.logbook_widget.setVisible(is_visible)
        self.show_logbook_action.setChecked(is_visible)

    def _calculate_band_from_frequency(self, frequency_str: str) -> Optional[str]:
        """
        Calculate band from frequency string, handling both kHz and MHz values

        Args:
            frequency_str: Frequency as string (can be kHz like "28482" or MHz like "28.482")

        Returns:
            Band string (e.g., "10m") or None if invalid
        """
        try:
            freq = float(frequency_str)
            # Convert kHz to MHz if needed (values > 1000 are likely kHz)
            if freq > 1000:
                freq_mhz = freq / 1000
            else:
                freq_mhz = freq

            return QSO.frequency_to_band(str(freq_mhz))
        except (ValueError, TypeError):
            return None

    def _get_power_for_mode(self, mode: str) -> Optional[int]:
        """
        Get configured power level for a given mode

        Args:
            mode: Mode string (USB, LSB, CW, FT8, etc.)

        Returns:
            Power level in watts, or None if not configured
        """
        mode_upper = mode.upper()

        # Determine mode category
        # SSB: USB, LSB, FM, AM (phone modes)
        if any(m in mode_upper for m in ['USB', 'LSB', 'FM', 'AM', 'SSB']):
            return self.settings.value("cat/power_ssb", None, type=int)

        # CW modes
        elif 'CW' in mode_upper:
            return self.settings.value("cat/power_cw", None, type=int)

        # Digital/Data modes: FT8, FT4, RTTY, PSK, DATA, etc.
        elif any(m in mode_upper for m in ['FT8', 'FT4', 'FT', 'RTTY', 'PSK', 'DATA', 'DIGI', 'MFSK', 'JT', 'JS8']):
            return self.settings.value("cat/power_data", None, type=int)

        # Unknown mode - return None to use radio's current setting
        return None
