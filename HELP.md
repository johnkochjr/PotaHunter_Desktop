# POTA Hunter - User Guide

## Table of Contents
- [Overview](#overview)
- [Getting Started](#getting-started)
- [Main Window](#main-window)
- [POTA Spots](#pota-spots)
- [Logbook](#logbook)
- [QRZ Integration](#qrz-integration)
- [CAT Control](#cat-control)
- [Filtering](#filtering)
- [Logging Contacts](#logging-contacts)
- [Import/Export](#importexport)
- [Settings](#settings)
- [Keyboard Shortcuts](#keyboard-shortcuts)

## Overview

POTA Hunter is a Parks on the Air (POTA) spotting and logging application designed to help amateur radio operators hunt and activate parks efficiently. The application provides real-time spot monitoring, integrated QRZ lookups, CAT control for compatible radios, and comprehensive logging capabilities.

**Version:** 0.1.0
**Built by:** JK Labs (https://johnkochjr.com)

## Getting Started

### Installation

1. Ensure Python 3.8 or higher is installed
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch the application:
   ```bash
   python -m potahunter.main
   ```

### First Time Setup

1. **Configure QRZ Credentials** (optional but recommended):
   - Go to **Tools → Settings**
   - Navigate to the **QRZ** tab
   - Enter your QRZ username and password
   - Optionally configure QRZ Logbook API key for automatic uploads

2. **Configure Station Information**:
   - Go to **Tools → Settings**
   - Navigate to the **Station** tab
   - Enter your callsign, location, and equipment details
   - This information will be automatically included in all QSO logs

3. **Configure CAT Control** (optional):
   - Go to **Tools → Settings**
   - Navigate to the **CAT Control** tab
   - Select your radio model and COM port
   - Enable CAT control to automatically tune your radio when clicking spots

## Main Window

The main window is divided into three primary sections:

### Left Panel - POTA Spots and Logbook
- **Top Section**: Live POTA spots from the POTA API
- **Bottom Section**: Your logbook showing recent contacts
- **Splitter**: Drag the divider to adjust the size of each section

### Right Panel - Callsign Information
- Displays detailed QRZ information for the selected callsign
- Shows QSL card image if available
- Fixed width to prevent jumping when content changes

### Status Bar
- Shows application status messages
- Displays loaded spots count
- Shows CAT connection status and current frequency

## POTA Spots

### Viewing Spots

The spots table displays real-time POTA activations with the following columns:

- **Time**: Minutes ago since the spot was posted (e.g., "5 min ago")
- **Callsign**: Activator's callsign, with QSO count if you've worked them before
- **Frequency**: Operating frequency in kHz
- **Mode**: Operating mode (CW, SSB, FT8, etc.)
- **Park**: Park reference with QSO count if you've worked it before
- **Location**: Park location description
- **Spotter**: Who spotted the activation

### Color Coding

Spots are color-coded by mode for easy identification:
- **Light Blue**: CW modes
- **Light Green**: Digital modes (FT8, FT4, RTTY, PSK31, etc.)
- **Navajo White**: Phone modes (SSB, USB, LSB, FM, AM)

### Sorting

- Click any column header to sort by that column
- Default sort is by Time (newest first)
- The time column sorts by actual timestamp, not the displayed relative time

### Auto-Refresh

- Spots automatically refresh every 60 seconds
- Toggle auto-refresh on/off using the **Auto-Refresh** button
- Manual refresh available via the **Refresh Spots** button

### Interacting with Spots

- **Single Click**: Select a spot to view QRZ information and filter logbook
- **Double Click**:
  - On Callsign/other columns: Opens logging dialog
  - On Park column: Opens park page on pota.app in your browser

### Selection Persistence

When spots refresh, your selected spot remains selected (stays on the same callsign/park combination).

## Logbook

### Viewing Your Log

The logbook section shows your most recent 50 contacts by default:

- **Date**: QSO date
- **Time**: QSO time (UTC)
- **Callsign**: Worked station's callsign
- **Frequency**: Contact frequency
- **Mode**: Operating mode
- **Band**: Operating band
- **RST Sent/Rcvd**: Signal reports
- **Park**: Park reference (if applicable)
- **Name**: Operator's name
- **QTH**: Location
- **State**: State/province
- **Comment**: QSO notes

### Auto-Filter Options

The **Auto-Filter** dropdown provides three modes:

- **None**: Shows all recent QSOs (no filtering)
- **Callsign**: Automatically filters to show QSOs with the selected spot's callsign
- **Park**: Automatically filters to show all QSOs from the selected park

When a filter is active, the logbook shows how many QSOs match (e.g., "3 of 150 QSOs").

### Full Logbook View

- Click **View Logbook** button or use **File → View Logbook** menu
- Opens a separate window with complete logbook access
- Sortable by any column
- Shows all QSOs (not limited to 50)

## QRZ Integration

### Automatic Lookups

When you click a spot:
1. A loading indicator appears
2. QRZ lookup is performed in the background
3. Results display within the loading time (minimum 300ms)
4. Callsign information and QSL card image (if available) are shown

### Information Displayed

- Callsign (clickable link to QRZ.com)
- Name
- Address (city, state, country)
- Grid square
- License class
- QSL information
- QSL card image (if available)

### Caching

QRZ lookups are cached for 1 hour to:
- Reduce API calls
- Improve performance
- Comply with QRZ API usage guidelines

### Configuration

Configure QRZ credentials in **Tools → Settings → QRZ**:
- Username and password for XML lookups
- API key for QRZ Logbook uploads
- Auto-upload option for new QSOs

## CAT Control

### Supported Features

- Automatic frequency tuning when clicking spots
- Automatic mode selection (USB/LSB/CW based on frequency)
- Real-time frequency and mode display
- Connection status indicator

### Setup

1. Go to **Tools → Settings → CAT Control**
2. Enable CAT control
3. Select your radio model from the dropdown
4. Select the COM port your radio is connected to
5. Select appropriate baud rate (or leave as Auto)
6. Click OK to save and connect

### Status Indicators

- **CAT: Disconnected** (gray): Radio not connected
- **CAT: Connected, Mode: USB** (green): Radio connected and communicating
- **Frequency Display**: Shows current radio frequency when connected

### Automatic Tuning

When CAT is enabled and you click a spot:
- Radio automatically tunes to the spot frequency
- Mode is automatically selected (USB for >10 MHz, LSB for <10 MHz, CW for CW spots)
- Status bar confirms the tuning operation

## Filtering

### Band Filter

Filter spots by amateur radio band:
- All Bands (default)
- 160m, 80m, 60m, 40m, 30m, 20m, 17m, 15m, 12m, 10m, 6m, 2m

### Mode Filter

Filter spots by mode category:
- All Modes (default)
- CW: All CW modes
- Digital: FT8, FT4, RTTY, PSK31, PSK63, JS8, MFSK, OLIVIA, CONTESTIA
- Phone: SSB, USB, LSB, FM, AM

### Search Filter

Free-text search that filters by:
- Park reference (e.g., "K-4566")
- Callsign (e.g., "W1AW")
- Location description (e.g., "Colorado")

### Clear Filters

Click the **Clear Filters** button to reset all filters to defaults.

## Logging Contacts

### Opening the Logging Dialog

Three ways to log a contact:
1. Double-click a spot (except park column)
2. Select a spot and press Enter
3. Right-click a spot (if context menu is implemented)

### Logging Dialog Fields

The logging dialog pre-fills information from the spot and QRZ lookup:

**Automatically Filled:**
- Callsign
- Frequency
- Mode
- Park reference
- Name (from QRZ)
- Date/Time (current UTC)

**Fields to Complete:**
- RST Sent (defaults based on mode)
- RST Rcvd
- QTH
- State/Province
- Comment
- Station callsign (from settings)
- My park reference (if activating)

### Saving QSOs

1. Fill in required fields
2. Click **Save** to add to logbook
3. QSO is immediately added to database
4. Logbook display refreshes automatically
5. If auto-upload is enabled, QSO is queued for QRZ upload

## Import/Export

### Importing ADIF Files

1. Go to **File → Import ADIF File**
2. Select an ADIF file (.adi or .adif)
3. File is validated for proper ADIF format
4. QSOs are imported into the database
5. Imported QSOs are marked as "uploaded" to prevent duplicate QRZ uploads
6. Summary shows how many QSOs were imported

**Supported ADIF Fields:**
- Standard QSO fields (callsign, date, time, frequency, mode, etc.)
- POTA-specific fields (park reference, my park reference)
- Station information fields
- Custom fields are preserved

### Exporting ADIF Files

1. Go to **File → Export Log (ADIF)** or click **Export Log** button
2. Choose save location and filename
3. All QSOs are exported in ADIF format
4. File can be imported into other logging software
5. Compatible with QRZ Logbook, LoTW, eQSL, etc.

**Export Format:**
- ADIF 3.x format
- All database fields included
- Proper ADIF headers and formatting
- Compatible with all major logging applications

### QRZ Logbook Upload

1. Configure QRZ API key in **Tools → Settings → QRZ**
2. Go to **Tools → Upload to QRZ Logbook** or click **Upload to QRZ Logbook** button
3. Dialog shows which QSOs will be uploaded (excludes already uploaded)
4. Click **Upload** to send to QRZ
5. Progress is displayed during upload
6. Successfully uploaded QSOs are marked to prevent duplicates

**Auto-Upload:**
- Enable in **Tools → Settings → QRZ**
- New QSOs are automatically uploaded after saving
- Reduces manual upload steps

## Settings

Access settings via **Tools → Settings** menu.

### QRZ Tab

- **Username**: QRZ username for XML API
- **Password**: QRZ password for XML API
- **API Key**: QRZ Logbook API key for uploads
- **Auto-Upload**: Enable automatic QSO uploads after logging

### Station Tab

Configure your station information (included in all logged QSOs):

- **Station Callsign**: Your callsign
- **Operator**: Operator name (if different)
- **Grid Square**: Maidenhead locator
- **Street, City, County, State**: Station location
- **Postal Code, Country**: Additional location
- **DXCC**: DXCC entity code
- **Latitude, Longitude**: Station coordinates
- **Rig**: Radio equipment description
- **Power**: Transmit power in watts
- **Antenna**: Antenna information

### CAT Control Tab

- **Enable CAT Control**: Toggle CAT functionality
- **Radio Model**: Select your radio from supported models
- **COM Port**: Serial port for radio connection
- **Baud Rate**: Communication speed (Auto recommended)

**Supported Radios:**
- Yaesu (FT-991A, FT-891, FT-991, FT-950, etc.)
- Icom (IC-7300, IC-7610, IC-9700, etc.)
- Kenwood (TS-590, TS-890, etc.)
- Elecraft (K3, KX3, KX2)
- And many more via Hamlib

## Keyboard Shortcuts

### Main Window
- **F5**: Refresh spots
- **Ctrl+L**: Open logbook viewer
- **Ctrl+E**: Export log to ADIF
- **Ctrl+S**: Open settings
- **Ctrl+Q**: Quit application

### Logging Dialog
- **Enter**: Save QSO
- **Escape**: Cancel/Close without saving
- **Tab**: Navigate between fields

## Tips and Best Practices

### Performance

1. **Enable QRZ caching**: Lookups are cached for 1 hour, reducing API calls
2. **Adjust refresh rate**: 60 seconds is a good balance between freshness and API load
3. **Use filters**: Reduce spot count for better performance with large spot lists

### Efficient Hunting

1. **Use color coding**: Quickly identify modes you're interested in
2. **Set up CAT control**: Automatically tune to spots with one click
3. **Enable auto-filter**: See if you've worked a station/park before clicking
4. **Use park filter**: Focus on parks you need for awards

### Logging

1. **Configure station info**: Pre-fills your information in every QSO
2. **Use QRZ lookups**: Automatically fills name and location
3. **Enable auto-upload**: Automatically syncs with QRZ Logbook
4. **Add comments**: Note conditions, antenna used, or other details

### Database Management

1. **Regular exports**: Export your log regularly as backup
2. **Import existing logs**: Consolidate logs from other software
3. **Review logbook**: Use full logbook viewer to sort and analyze QSOs

## Troubleshooting

### QRZ Lookups Not Working

- Verify credentials in **Tools → Settings → QRZ**
- Check internet connection
- Ensure QRZ subscription is active (XML access required)
- Check application logs for error messages

### CAT Control Issues

- Verify correct COM port selected
- Check USB cable connection
- Ensure radio is powered on
- Try different baud rates if Auto doesn't work
- Check radio's CAT settings (may need to enable)
- Close other applications using the same COM port

### Spots Not Refreshing

- Check internet connection
- Verify POTA API is accessible (https://api.pota.app)
- Check if auto-refresh is enabled
- Try manual refresh

### Database Issues

- Database file location: `~/.potahunter/potahunter.db`
- Backup regularly by exporting to ADIF
- If corrupted, delete database file (will lose logs - export first!)

## Support and Contributing

- **Issues**: Report bugs at https://github.com/anthropics/PotaHunter/issues
- **Website**: https://johnkochjr.com
- **License**: MIT License

## Acknowledgments

POTA Hunter uses:
- POTA API for real-time spots
- QRZ XML API for callsign lookups
- PySide6 for the user interface
- Hamlib for CAT control

Thanks to the POTA community for making amateur radio activations fun and accessible!

---

**73 and happy hunting!**