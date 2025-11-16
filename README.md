# POTA Hunter

A cross-platform desktop application for Parks on the Air (POTA) spotting and logging, built with Python and PySide6.

## Features

### Spotting
- **Real-time POTA Spot Monitoring**: Automatically fetch and display active POTA spots from the POTA API
- **Color Coding**: Visual mode identification (CW=Blue, Digital=Green, Phone=Tan)
- **Powerful Filtering**: Filter by band, mode, or search for specific parks/callsigns
- **Smart Actions**: Double-click park to view on pota.app, or any other column to log the contact
- **Auto-refresh**: Configurable automatic spot refresh (60 seconds)

### QRZ Integration
- **Real-time Callsign Lookup**: Detailed operator information from QRZ.com (requires XML subscription)
- **QSL Card Display**: View operator's QSL card image directly in the app
- **Clickable Links**: Callsigns, emails, and QSL managers are clickable for easy access
- **Auto-prefill Names**: Operator names automatically filled in logging dialog
- **QRZ Logbook Upload**: Upload QSOs to QRZ Logbook with bulk or automatic upload options

### Logging & Logbook
- **Quick Logging**: Pre-filled logging dialog with spot data and QRZ information
- **Auto-Upload**: Optional automatic upload to QRZ Logbook when saving QSOs
- **Logbook Viewer**: View all logged QSOs in a sortable, searchable table with band display
- **Edit Contacts**: Double-click any QSO to edit all fields
- **Bulk Operations**: Multi-select QSOs and delete multiple contacts at once
- **Upload Tracking**: Visual indicators show which QSOs have been uploaded to QRZ
- **Local Database**: Store all your QSOs in a local SQLite database

### Export & Integration
- **ADIF Export**: Export your logs in standard ADIF format for importing into other logging software
- **QRZ Logbook Upload**: Upload QSOs to QRZ Logbook with selective or bulk upload
- **Automatic Band Calculation**: Frequency-to-band conversion for all QSOs
- **LoTW Integration**: ARRL LoTW upload (coming soon)

## Requirements

- Python 3.8 or higher
- Windows, macOS, or Linux
- Optional: QRZ.com XML subscription for callsign lookups
- Optional: QRZ Logbook API key for log uploads (get from https://logbook.qrz.com/api)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/PotaHunter.git
cd PotaHunter
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Option 1: Run from Source

From the project root directory:

```bash
python run.py
```

If you're using a virtual environment:

```bash
# On Windows:
venv\Scripts\python.exe run.py

# On macOS/Linux:
./venv/bin/python run.py
```

### Option 2: Build Standalone Executable

You can build a standalone executable that doesn't require Python to be installed:

```bash
# On macOS/Linux:
./build_executable.sh

# On Windows:
build_executable.bat
```

After building:
- **macOS**: Run `dist/PotaHunter.app`
- **Windows**: Run `dist\PotaHunter\PotaHunter.exe`
- **Linux**: Run `dist/PotaHunter/PotaHunter`

See [BUILD.md](BUILD.md) for detailed build instructions and distribution options.

## Usage

### Viewing Spots

- The main window displays current POTA spots in a sortable table
- Click column headers to sort by that field
- Click "Refresh Spots" to manually update the spot list
- Toggle "Auto-Refresh" to enable/disable automatic updates (default: every 60 seconds)

### Logging a Contact

1. Double-click any spot in the table to open the logging dialog
2. The dialog will be pre-filled with:
   - Callsign
   - Frequency
   - Mode
   - Park reference
   - Location
   - Current UTC date/time
3. Fill in additional information:
   - RST sent/received (defaults to 59)
   - Name
   - Grid square
   - Comments
   - Your grid square
4. Click "Save QSO" to save the contact to your local database

### Viewing Your Logbook

1. Click "View Logbook" button or use File → View Logbook
2. Browse all your logged QSOs in a sortable table
3. **Edit a QSO**: Double-click any row to edit contact details
4. **Delete QSOs**:
   - Right-click single QSO → Delete QSO
   - Select multiple QSOs (Ctrl/Cmd+Click) → Right-click → Delete X QSOs
5. All changes are saved immediately to the database

### Exporting Your Log

1. Click "Export Log (ADIF)" or use File → Export Log
2. Choose a location to save your ADIF file
3. The exported file can be imported into other logging software or uploaded to QRZ/LoTW

### QRZ Integration Setup

1. Go to Tools → Settings
2. Enter your QRZ.com username and password
3. Click "Test Credentials" to verify (requires active QRZ XML subscription)
4. Click "Save" to enable real-time callsign lookups
5. Click any spot to see operator information and QSL card (if available)

### QRZ Logbook Upload

#### Manual Bulk Upload

1. Click "Upload to QRZ Logbook" button or use File → Upload to QRZ Logbook
2. The upload dialog shows all QSOs with checkboxes for selection
3. Use the selection buttons:
   - **Select All**: Select all QSOs
   - **Select None**: Deselect all QSOs
   - **Select Unuploaded**: Auto-select only QSOs not yet uploaded (recommended)
4. Previously uploaded QSOs are highlighted in light green
5. Optional: Enter a station callsign if different from your QRZ account
6. Click "Upload Selected" to upload to QRZ Logbook
7. View upload results showing success/failure counts

#### Automatic Upload

1. Go to Tools → Settings
2. Enter your QRZ Logbook API key
3. Check "Automatically upload QSOs to QRZ Logbook when saving"
4. Click "Save"
5. From now on, all QSOs will be automatically uploaded when you save them
6. Upload status is displayed in the save confirmation message

**Note**: The auto-upload checkbox is only enabled when you have a valid API key configured.

## Project Structure

```
PotaHunter/
├── src/
│   └── potahunter/
│       ├── __init__.py
│       ├── main.py              # Application entry point
│       ├── ui/                  # User interface components
│       │   ├── __init__.py
│       │   ├── main_window.py   # Main application window
│       │   ├── logging_dialog.py # QSO logging dialog
│       │   ├── logbook_viewer.py # Logbook viewer window
│       │   ├── qso_edit_dialog.py # QSO edit/delete dialog
│       │   ├── qrz_upload_dialog.py # QRZ upload dialog
│       │   └── settings_dialog.py # Settings dialog
│       ├── services/            # External API services
│       │   ├── __init__.py
│       │   ├── pota_api.py      # POTA API integration
│       │   ├── qrz_api.py       # QRZ XML API integration
│       │   └── qrz_upload.py    # QRZ Logbook upload service
│       ├── models/              # Data models
│       │   ├── __init__.py
│       │   ├── qso.py           # QSO data model
│       │   └── database.py      # Database manager
│       └── utils/               # Utility functions
│           ├── __init__.py
│           ├── adif_export.py   # ADIF export utilities
│           └── migrate_bands.py # Band migration script
├── tests/                       # Unit tests
├── data/                        # Local database storage
├── requirements.txt             # Python dependencies
├── run.py                       # Application launcher
└── README.md                    # This file
```

## Data Storage

- **QSO Database**: QSOs are stored in a SQLite database at `data/potahunter.db`
- **Settings**: QRZ credentials and preferences are stored using platform-native settings (macOS: ~/Library/Preferences, Windows: Registry, Linux: ~/.config)
- The database is created automatically on first run
- **Backup**: Backup your `data/` directory to preserve your log

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/
```

### Linting

```bash
pylint src/potahunter/
```

## Roadmap

- [x] Real-time POTA spot display
- [x] Local QSO logging
- [x] Logbook viewer with edit/delete
- [x] Multi-select and bulk delete
- [x] QRZ XML API integration
- [x] QSL card image display
- [x] Color-coded modes
- [x] Filter spots by band, mode, or location
- [x] User preferences/settings dialog
- [x] ADIF export
- [x] QRZ Logbook upload with bulk and auto-upload
- [x] Automatic band calculation from frequency
- [x] Upload tracking and visual indicators
- [ ] Grid square calculation from park location
- [ ] LoTW upload via TQSL
- [ ] Duplicate contact checking
- [ ] Log statistics and analytics
- [ ] Map view of active parks

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Parks on the Air](https://parksontheair.com/) for the POTA program and API
- [PySide6](https://doc.qt.io/qtforpython/) for the GUI framework
- The amateur radio community for inspiration and support

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

73 de POTA Hunter Team
