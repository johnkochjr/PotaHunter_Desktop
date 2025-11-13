# POTA Hunter - Quick Start Guide

## First Time Setup

### 1. Install Python
Make sure you have Python 3.8 or higher installed:
```bash
python --version
```

### 2. Create Virtual Environment
```bash
# Navigate to project directory
cd PotaHunter

# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Running the Application

### Simple Method (Recommended)
```bash
python run.py
```

### Alternative Methods

**From src directory:**
```bash
cd src
python -m potahunter.main
```

**Using setup.py (install mode):**
```bash
pip install -e .
potahunter
```

## First Steps

1. **View Spots**: The application will automatically fetch POTA spots when it starts
2. **Sort Spots**: Click any column header to sort the table
3. **View Park Info**: Double-click the Park column to open the park page in your browser
4. **Log a Contact**: Double-click on any other column (Callsign, Frequency, etc.) to open the logging dialog
5. **Fill Details**: Add RST, name, grid square, and any comments
6. **Save**: Click "Save QSO" to store in your local database

## Features Overview

### Main Window
- **Refresh Spots**: Manually update the spot list
- **Auto-Refresh Toggle**: Enable/disable automatic updates (60 second interval)
- **Export Log**: Export all QSOs to ADIF format
- **Upload**: Upload logs to QRZ/LoTW (coming soon)

### Logging Dialog
Pre-filled from spot:
- Callsign
- Frequency
- Mode
- Park Reference
- Location

You should add:
- RST Sent/Received (defaults to 59)
- Name (optional)
- Grid Square (if known)
- Your Grid Square
- Comments (optional)

## Data Storage

Your QSO log is stored in:
```
PotaHunter/data/potahunter.db
```

**Important**: Backup this file regularly to preserve your log!

## Exporting Your Log

1. Click "Export Log (ADIF)" button
2. Choose where to save the file
3. The .adi file can be imported into:
   - QRZ Logbook
   - LoTW (via TQSL)
   - Any ADIF-compatible logging software

## Mouse Actions

- **Double-click Park column**: Opens park page on pota.app in your browser
- **Double-click any other column**: Opens logging dialog with pre-filled data
- **Click column header**: Sort table by that column

## Keyboard Shortcuts

- **Enter**: Open logging dialog for selected spot
- **F5**: Refresh spots
- **Ctrl+E**: Export log
- **Ctrl+Q**: Quit application

## Troubleshooting

### Application won't start
- Make sure virtual environment is activated
- Verify all dependencies are installed: `pip list`
- Check Python version: `python --version` (must be 3.8+)

### No spots appearing
- Check your internet connection
- The POTA API may be temporarily down
- Try clicking "Refresh Spots"

### Can't save QSO
- Ensure required fields are filled: Callsign, Frequency, Mode, Date, Time
- Check that the data directory exists and is writable

## Tips

1. **Auto-Refresh**: Keep it ON to always see the latest spots
2. **Sorting**: Click frequency column to group by band
3. **Quick Logging**: Double-click is faster than selecting and clicking
4. **Regular Exports**: Export your log periodically for backup
5. **Grid Squares**: If you don't know a grid square, leave it blank

## Next Steps

- Configure your station information (Settings - coming soon)
- Set up QRZ/LoTW credentials (coming soon)
- Explore filtering options (coming soon)
- Check out the statistics view (coming soon)

## Getting Help

- Read the full [README.md](README.md)
- Check the [GitHub Issues](https://github.com/yourusername/PotaHunter/issues)
- Join the POTA community

## Happy Hunting!

73 de POTA Hunter Team
