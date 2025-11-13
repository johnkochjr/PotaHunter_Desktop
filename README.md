# POTA Hunter

A cross-platform desktop application for Parks on the Air (POTA) spotting and logging, built with Python and PySide6.

## Features

- **Real-time POTA Spot Monitoring**: Automatically fetch and display active POTA spots from the POTA API
- **QRZ Integration**: Real-time callsign lookup with detailed operator information (requires QRZ XML subscription)
- **Smart Actions**: Double-click park to view on pota.app, or any other column to log the contact
- **Color Coding**: Visual mode identification (CW=Blue, Digital=Green, Phone=Tan)
- **Powerful Filtering**: Filter by band, mode, or search for specific parks/callsigns
- **Quick Logging**: Pre-filled logging dialog with spot data
- **Local Database**: Store all your QSOs in a local SQLite database
- **ADIF Export**: Export your logs in standard ADIF format for importing into other logging software
- **QRZ/LoTW Integration**: Upload logs directly to QRZ Logbook or ARRL LoTW (coming soon)
- **Auto-refresh**: Configurable automatic spot refresh (60 seconds)

## Requirements

- Python 3.8 or higher
- Windows, macOS, or Linux
- Optional: QRZ.com XML subscription for callsign lookups

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

### Exporting Your Log

1. Click "Export Log (ADIF)" or use File → Export Log
2. Choose a location to save your ADIF file
3. The exported file can be imported into other logging software or uploaded to QRZ/LoTW

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
│       │   └── logging_dialog.py # QSO logging dialog
│       ├── services/            # External API services
│       │   ├── __init__.py
│       │   └── pota_api.py      # POTA API integration
│       ├── models/              # Data models
│       │   ├── __init__.py
│       │   ├── qso.py           # QSO data model
│       │   └── database.py      # Database manager
│       └── utils/               # Utility functions
│           ├── __init__.py
│           └── adif_export.py   # ADIF export utilities
├── tests/                       # Unit tests
├── data/                        # Local database storage
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Data Storage

- QSOs are stored in a SQLite database located at `data/potahunter.db`
- The database is created automatically on first run
- Backup your `data/` directory to preserve your log

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
- [x] ADIF export
- [ ] Grid square calculation from park location
- [ ] QRZ Logbook upload
- [ ] LoTW upload via TQSL
- [ ] Duplicate contact checking
- [ ] Log statistics and analytics
- [ ] Configurable refresh intervals
- [ ] Filter spots by band, mode, or location
- [ ] Map view of active parks
- [ ] User preferences/settings dialog

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
