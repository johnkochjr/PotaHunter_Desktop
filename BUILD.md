# Building POTA Hunter Executable

This guide explains how to build standalone executable packages for POTA Hunter that don't require Python to be installed.

## Overview

POTA Hunter can be packaged into standalone executables for:
- **macOS**: `.app` bundle
- **Windows**: `.exe` executable
- **Linux**: Standalone binary

Users can run these executables without installing Python or any dependencies.

## Prerequisites

1. **Python 3.8 or higher** (for building only, not for end users)
2. **PyInstaller** (automatically installed by build script)
3. **All project dependencies** installed

### Install Dependencies

```bash
# Install all dependencies including PyInstaller
pip install -r requirements.txt
```

## Building on macOS

### Quick Build

```bash
./build_executable.sh
```

### Manual Build

```bash
# Install PyInstaller if not already installed
pip install pyinstaller

# Clean previous builds
rm -rf build/ dist/

# Build the app
pyinstaller PotaHunter.spec

# Your app will be at: dist/PotaHunter.app
```

### Installing on macOS

```bash
# Copy to Applications folder
cp -r dist/PotaHunter.app /Applications/

# Or run directly
open dist/PotaHunter.app
```

### Distribution

The entire `dist/PotaHunter.app` folder is the application. You can:
1. Zip it: `zip -r PotaHunter-macOS.zip dist/PotaHunter.app`
2. Create a DMG installer (see Advanced section)
3. Share the .app directly

## Building on Windows

### Quick Build

```cmd
build_executable.bat
```

### Manual Build

```cmd
REM Install PyInstaller if not already installed
pip install pyinstaller

REM Clean previous builds
rmdir /s /q build
rmdir /s /q dist

REM Build the executable
pyinstaller PotaHunter.spec
```

### Running on Windows

```cmd
dist\PotaHunter\PotaHunter.exe
```

### Distribution

The entire `dist\PotaHunter\` folder needs to be distributed. You can:
1. Zip it: Create `PotaHunter-Windows.zip` containing the folder
2. Create an installer using Inno Setup (see Advanced section)
3. Share the folder directly

## Building on Linux

### Quick Build

```bash
./build_executable.sh
```

### Manual Build

```bash
# Install PyInstaller if not already installed
pip install pyinstaller

# Clean previous builds
rm -rf build/ dist/

# Build the executable
pyinstaller PotaHunter.spec

# Your executable will be at: dist/PotaHunter/PotaHunter
```

### Running on Linux

```bash
chmod +x dist/PotaHunter/PotaHunter
./dist/PotaHunter/PotaHunter
```

### Distribution

The entire `dist/PotaHunter/` directory needs to be distributed. You can:
1. Create a tarball: `tar -czf PotaHunter-Linux.tar.gz dist/PotaHunter`
2. Create a .deb or .rpm package (see Advanced section)
3. Share the directory directly

## Build Output

After building, you'll have:

```
dist/
├── PotaHunter.app/          # macOS (if building on macOS)
│   └── Contents/
│       └── MacOS/
│           └── PotaHunter
└── PotaHunter/              # Windows/Linux (if building on Windows/Linux)
    ├── PotaHunter.exe       # Windows executable
    ├── PotaHunter           # Linux executable
    └── [various libraries and dependencies]
```

## Customization

### Adding an Icon

1. **macOS**: Create `icon.icns` file
2. **Windows**: Create `icon.ico` file
3. **Linux**: Create `icon.png` file

Then update `PotaHunter.spec`:

```python
exe = EXE(
    ...
    icon='icon.icns',  # or 'icon.ico' for Windows
)
```

### App Information

Edit `PotaHunter.spec` to customize:
- App name
- Version number
- Bundle identifier (macOS)
- Company name

## Troubleshooting

### Build Fails with Missing Modules

If PyInstaller can't find some modules, add them to `hiddenimports` in `PotaHunter.spec`:

```python
hiddenimports=[
    'PySide6.QtCore',
    'your_missing_module',
],
```

### App Won't Start

1. Test by running with console enabled first:
   - In `PotaHunter.spec`, set `console=True`
   - Rebuild and check console output for errors

2. Check that all dependencies are included:
   ```bash
   pyinstaller --clean PotaHunter.spec
   ```

### macOS Security Warning

When distributing macOS apps, users may see "App is damaged" warning. To fix:

1. **Code sign the app** (requires Apple Developer account):
   ```bash
   codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/PotaHunter.app
   ```

2. **Notarize the app** (requires Apple Developer account):
   ```bash
   xcrun notarytool submit PotaHunter.zip --apple-id your@email.com --wait
   xcrun stapler staple dist/PotaHunter.app
   ```

3. **Without code signing**, users can run:
   ```bash
   xattr -cr /path/to/PotaHunter.app
   ```

### Windows Antivirus False Positives

Some antivirus software may flag PyInstaller executables. To reduce this:

1. Code sign your executable (requires code signing certificate)
2. Submit to antivirus vendors for whitelisting
3. Build with `upx=False` in spec file

## Advanced

### Creating macOS DMG Installer

Install `create-dmg`:

```bash
brew install create-dmg

# Create DMG
create-dmg \
  --volname "POTA Hunter" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "PotaHunter.app" 200 190 \
  --hide-extension "PotaHunter.app" \
  --app-drop-link 600 185 \
  "PotaHunter-macOS.dmg" \
  "dist/"
```

### Creating Windows Installer

Install Inno Setup, then create `installer.iss`:

```ini
[Setup]
AppName=POTA Hunter
AppVersion=1.0.0
DefaultDirName={pf}\PotaHunter
DefaultGroupName=POTA Hunter
OutputDir=.
OutputBaseFilename=PotaHunter-Setup

[Files]
Source: "dist\PotaHunter\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\POTA Hunter"; Filename: "{app}\PotaHunter.exe"
Name: "{commondesktop}\POTA Hunter"; Filename: "{app}\PotaHunter.exe"
```

### Single-File Executable

To create a single-file executable (larger but simpler distribution), modify `PotaHunter.spec`:

```python
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,      # Add this
    a.zipfiles,      # Add this
    a.datas,         # Add this
    [],
    name='PotaHunter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)

# Remove or comment out the COLLECT section
```

## Continuous Integration

### GitHub Actions Example

Create `.github/workflows/build.yml`:

```yaml
name: Build Executables

on:
  release:
    types: [created]

jobs:
  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: ./build_executable.sh
      - uses: actions/upload-artifact@v3
        with:
          name: PotaHunter-macOS
          path: dist/PotaHunter.app

  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: ./build_executable.bat
      - uses: actions/upload-artifact@v3
        with:
          name: PotaHunter-Windows
          path: dist/PotaHunter

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: ./build_executable.sh
      - uses: actions/upload-artifact@v3
        with:
          name: PotaHunter-Linux
          path: dist/PotaHunter
```

## File Size

Typical executable sizes:
- **macOS**: ~100-150 MB (includes Qt frameworks)
- **Windows**: ~80-120 MB
- **Linux**: ~80-120 MB

To reduce size:
- Set `upx=True` in spec file (already enabled)
- Remove unused dependencies
- Use `--exclude-module` for large unused packages

## Testing

Always test the built executable on a clean machine (without Python installed):

1. Copy the executable to a test machine
2. Run it to ensure all dependencies are included
3. Test all features, especially file operations and network requests
4. Check that settings are saved correctly

## Support

For build issues:
1. Check PyInstaller documentation: https://pyinstaller.org/
2. Review common issues: https://github.com/pyinstaller/pyinstaller/wiki
3. Open an issue on the POTA Hunter GitHub repository

73!
