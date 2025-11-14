"""
Main window for POTA Hunter application
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QStatusBar, QMenuBar, QMenu, QComboBox, QLabel, QCheckBox,
    QTextEdit, QGroupBox, QSplitter, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, QUrl, QSettings, QByteArray
from PySide6.QtGui import QAction, QColor, QBrush, QDesktopServices, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from potahunter.services.pota_api import PotaAPIService
from potahunter.services.qrz_api import QRZAPIService
from potahunter.ui.logging_dialog import LoggingDialog
from potahunter.ui.settings_dialog import SettingsDialog
from potahunter.ui.logbook_viewer import LogbookViewer

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
        self.all_spots = []  # Store all spots for filtering
        self.settings = QSettings()
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.on_image_downloaded)
        self.current_qrz_info = {}  # Store current callsign's QRZ info
        self.load_qrz_credentials()
        self.init_ui()
        self.setup_refresh_timer()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("POTA Hunter - Spots & Logging")
        self.setGeometry(100, 100, 1200, 700)

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

        button_layout.addStretch()

        self.logbook_button = QPushButton("View Logbook")
        self.logbook_button.clicked.connect(self.open_logbook)
        button_layout.addWidget(self.logbook_button)

        self.export_button = QPushButton("Export Log (ADIF)")
        self.export_button.clicked.connect(self.export_log)
        button_layout.addWidget(self.export_button)

        self.upload_button = QPushButton("Upload to QRZ/LoTW")
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

        # Create splitter for table and details panel
        splitter = QSplitter(Qt.Horizontal)

        # Spots table
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

        # Single-click handler - lookup callsign info
        self.spots_table.currentItemChanged.connect(self.on_row_selection_changed)

        splitter.addWidget(self.spots_table)

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

        splitter.addWidget(details_widget)

        # Set initial splitter sizes (70% table, 30% details)
        splitter.setSizes([700, 300])

        layout.addWidget(splitter)

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

        upload_action = QAction("&Upload to QRZ/LoTW", self)
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

        dialog = LoggingDialog(spot_data, self)
        dialog.exec()

    def export_log(self):
        """Export log to ADIF file"""
        self.status_bar.showMessage("Export functionality coming soon...", 3000)
        # TODO: Implement ADIF export

    def upload_log(self):
        """Upload log to QRZ/LoTW"""
        self.status_bar.showMessage("Upload functionality coming soon...", 3000)
        # TODO: Implement upload

    def open_logbook(self):
        """Open logbook viewer window"""
        logbook_window = LogbookViewer(self)
        logbook_window.show()
        self.status_bar.showMessage("Opened logbook viewer", 2000)

    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self)

        # Load current credentials
        username = self.settings.value("qrz/username", "")
        password = self.settings.value("qrz/password", "")
        dialog.set_qrz_credentials(username, password)

        if dialog.exec():
            # Save credentials
            username, password = dialog.get_qrz_credentials()
            self.settings.setValue("qrz/username", username)
            self.settings.setValue("qrz/password", password)

            # Update QRZ service
            self.qrz_service.set_credentials(username, password)

            if username and password:
                self.status_bar.showMessage("QRZ credentials saved", 3000)
            else:
                self.status_bar.showMessage("QRZ credentials cleared", 3000)

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

    def on_row_selection_changed(self, current, previous):
        """
        Handle row selection change - lookup callsign info from QRZ

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
