========================================
POTA Hunter - Testing Instructions
========================================

Thank you for testing POTA Hunter!

INSTALLATION
------------

1. Unzip the file you received (PotaHunter-macOS.zip)
2. You should see a folder called "dist" containing:
   - PotaHunter.app
   - launch_potahunter.sh
   - PotaHunter folder (with support files)

RUNNING THE APPLICATION
-----------------------

Option 1 (Recommended):
  Open Terminal, navigate to the dist folder, and run:
  ./launch_potahunter.sh

Option 2:
  In Terminal:
  ./PotaHunter.app/Contents/MacOS/PotaHunter

Option 3 (if you get security warnings):
  In Terminal, run these commands first:
  xattr -cr PotaHunter.app
  ./launch_potahunter.sh

FIRST-TIME SETUP
----------------

When you first run POTA Hunter:

1. The app will create a local database in the "data" folder
2. Go to Tools → Settings to configure (optional):
   - QRZ.com username/password (for callsign lookups)
   - QRZ Logbook API key (for automatic log uploads)

TESTING CHECKLIST
-----------------

Please test the following features and report any issues:

[ ] Application launches successfully
[ ] Main window displays POTA spots
[ ] Click "Refresh Spots" to update spot list
[ ] Sort spots by clicking column headers
[ ] Filter spots by band, mode, or search text
[ ] Double-click a spot to open logging dialog
[ ] Log a QSO and save it
[ ] View your logbook (View Logbook button)
[ ] Edit a QSO in the logbook (double-click)
[ ] Delete a QSO (right-click)
[ ] Export log to ADIF format
[ ] Settings dialog (Tools → Settings)
[ ] QRZ integration (if you have QRZ.com account)
[ ] Auto-refresh toggle works

KNOWN ISSUES
------------

- Double-clicking PotaHunter.app may not work on some Macs
  → Solution: Use the launch_potahunter.sh script instead

- macOS security warning about unidentified developer
  → Solution: Run "xattr -cr PotaHunter.app" in Terminal first

REPORTING ISSUES
----------------

When reporting issues, please include:

1. What you were trying to do
2. What happened (include any error messages)
3. Your macOS version
4. Steps to reproduce the issue

REQUIREMENTS
------------

- macOS 10.13 or later
- No Python installation required
- Optional: QRZ.com XML subscription for callsign lookups
- Optional: QRZ Logbook API key for log uploads

Thank you for helping test POTA Hunter!
73!
