# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for POTA Hunter (One-File Mode)
This creates a single executable file.
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all PySide6 plugins
pyside6_datas = collect_data_files('PySide6')

# Include resources directory if it exists
import os
resources_path = os.path.join('src', 'potahunter', 'resources')
additional_datas = []
if os.path.exists(resources_path):
    additional_datas.append((resources_path, 'potahunter/resources'))

a = Analysis(
    ['run.py'],
    pathex=['src'],  # Add src directory to Python path
    binaries=[],
    datas=pyside6_datas + additional_datas,
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtNetwork',
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'idna',
        'potahunter',
        'potahunter.ui',
        'potahunter.services',
        'potahunter.models',
        'potahunter.utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PotaHunter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for GUI app (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/potahunter/resources/icon.ico',  # Windows icon (will be ignored if file doesn't exist)
)

# macOS app bundle
if sys.platform == 'darwin':
    # Import version info
    sys.path.insert(0, 'src')
    from potahunter.version import __version__, APP_NAME, APP_DISPLAY_NAME, APP_BUNDLE_ID

    app = BUNDLE(
        exe,
        name='PotaHunter.app',
        icon='src/potahunter/resources/icon.icns',  # macOS icon (will be ignored if file doesn't exist)
        bundle_identifier=APP_BUNDLE_ID,
        info_plist={
            'CFBundleName': APP_NAME,
            'CFBundleDisplayName': APP_DISPLAY_NAME,
            'CFBundleVersion': __version__,
            'CFBundleShortVersionString': __version__,
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.13.0',
        },
    )
