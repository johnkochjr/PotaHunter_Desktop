# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for POTA Hunter
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all PySide6 plugins
pyside6_datas = collect_data_files('PySide6')

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=pyside6_datas,
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
    [],
    exclude_binaries=True,
    name='PotaHunter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to False for GUI app (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one: 'icon.icns' for macOS or 'icon.ico' for Windows
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PotaHunter',
)

# macOS app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='PotaHunter.app',
        icon=None,  # Add 'icon.icns' if you have one
        bundle_identifier='com.potahunter.app',
        info_plist={
            'CFBundleName': 'POTA Hunter',
            'CFBundleDisplayName': 'POTA Hunter',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.13.0',
        },
    )
