# POTA Hunter Features

## ADIF Import/Export

POTA Hunter supports importing and exporting your logbook in ADIF format:

### Import ADIF Files

Import contacts from other logging software or previous logs:

- **File → Import ADIF File** - Import QSOs from .adi or .adif files
- Supports standard ADIF 3.1.4 format
- Automatically validates file format before import
- **Auto-Protection**: All imported QSOs are automatically marked as "uploaded" to prevent duplicate uploads to QRZ Logbook
- Preserves all contact details including:
  - Basic QSO information (callsign, frequency, mode, date/time)
  - Station information (name, QTH, state, grid square)
  - POTA park references (from SIG/SIG_INFO fields)
  - My station information
  - Comments and notes
- Shows detailed import summary with success/error counts
- Imported QSOs immediately appear in the integrated logbook

**Use Cases:**
- Migrate from other logging software
- Import paper logs you've digitized
- Restore from backups
- Consolidate logs from multiple sources

### Export ADIF Files

Export your entire logbook to ADIF format:

- **File → Export Log (ADIF)** - Export all QSOs to .adi file
- Standard ADIF 3.1.4 format
- Compatible with:
  - QRZ Logbook
  - LoTW (via TQSL)
  - Other amateur radio logging software
- Includes all contact details and POTA-specific fields
- Exports with proper POTA SIG/SIG_INFO fields for park activations

## QRZ Integration

Real-time callsign lookup using the QRZ XML API:

- **Automatic Lookup** - Single-click any spot to instantly see callsign information
- **Details Panel** - Right-side panel displays operator details from QRZ
- **Information Shown**:
  - Operator name and location
  - Address and grid square
  - License class
  - QSL preferences (eQSL, LoTW, Mail)
  - CQ/ITU zones
  - QSL manager (if applicable)

**Setup:**
1. Go to Tools → Settings
2. Enter your QRZ.com username and password
3. Requires active QRZ XML subscription
4. Credentials are saved locally

Once configured, simply click any row in the spots table and the operator's information will appear in the right panel!

## Smart Double-Click Actions

The spots table supports context-aware double-click actions:

- **Double-click Park column** - Opens the park page on pota.app in your browser
  - Example: Double-clicking "K-0178" opens https://pota.app/#/park/K-0178
  - Shows park details, location, and activation history

- **Double-click any other column** - Opens the logging dialog
  - Pre-fills callsign, frequency, mode, park, and location
  - Ready to log your contact

This makes it easy to quickly get park information or log a contact without extra clicks!

## Color Coding

The main spots table uses color coding to quickly identify mode types:

- **Light Blue** - CW modes
- **Light Green** - Digital modes (FT8, FT4, RTTY, PSK31, JS8, etc.)
- **Navajo White/Tan** - Phone modes (SSB, USB, LSB, FM, AM)

The color legend is displayed above the spots table for easy reference.

## Filtering System

### Band Filter
Filter spots by amateur radio band:
- All Bands (default)
- 160m, 80m, 60m, 40m, 30m
- 20m, 17m, 15m, 12m, 10m
- 6m, 2m

The filter uses frequency-to-band conversion to match spots to the selected band.

### Mode Filter
Filter spots by mode category:
- **All Modes** (default)
- **CW** - Morse code
- **Digital** - FT8, FT4, RTTY, PSK31, PSK63, JS8, MFSK, OLIVIA, CONTESTIA
- **Phone** - SSB, USB, LSB, FM, AM

### Search Filter
Free-text search that matches against:
- Park reference (e.g., "K-0001", "VE-0123")
- Activator callsign (e.g., "W1AW", "K0XYZ")
- Park location/description

The search is case-insensitive and uses partial matching.

### Clear Filters Button
Instantly reset all filters to their default settings (All Bands, All Modes, empty search).

## Filter Behavior

- Filters are applied in real-time as you change selections
- Multiple filters can be combined (e.g., "20m + Digital" or "40m + CW")
- Status bar shows "Showing X of Y spots" when filters are active
- Filters persist during auto-refresh (filtered view is maintained)
- Sorting works with filtered results

## Usage Tips

1. **Quick Band Selection**: Click the band filter dropdown to focus on your favorite band
2. **Mode Hunting**: Use the mode filter to find specific digital or CW activations
3. **Park Search**: Type a park reference like "K-4" to find all parks starting with K-4
4. **Callsign Search**: Type a friend's callsign to see if they're activating
5. **Combined Filters**: Try "20m + Digital" to find all FT8/FT4 spots on 20 meters
6. **Clear View**: Click "Clear Filters" to return to viewing all spots

## Technical Details

### Color Coding Implementation
- Colors are applied at the table cell level using QBrush
- Mode detection supports exact matches and category matching
- Unknown modes display without color coding

### Filter Implementation
- Filters operate on a cached list of all spots
- Frequency-to-band conversion uses standard amateur radio band plans
- Search is case-insensitive and uses substring matching
- Filters are chainable and applied sequentially

### Performance
- Filtering is performed in-memory (very fast)
- No API calls are made when changing filters
- Table updates use Qt's efficient item system
- Auto-refresh preserves current filter settings

## Future Enhancements

Potential additions to the filtering system:
- [ ] Save/load filter presets
- [ ] Recent searches dropdown
- [ ] Advanced filters (by state, country, spots age)
- [ ] Filter by "new parks only" (not worked before)
- [ ] Highlight specific callsigns or parks
- [ ] Custom color schemes
- [ ] Filter by distance from your location
