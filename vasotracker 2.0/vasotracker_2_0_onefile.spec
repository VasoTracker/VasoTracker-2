# -*- mode: python ; coding: utf-8 -*-

import sys
sys.setrecursionlimit(sys.getrecursionlimit() * 5)

added_files = [("images", "images"), ("SampleData", "SampleData"), ('settings.toml', '.')]

a = Analysis(
    ['vasotracker_2_0.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=['PyDAQmx', 'scipy'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    # Note: The 'exclude_binaries' is set to False to include all binaries in the single executable
    exclude_binaries=False,
    name='vasotracker_2_0',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
    icon='C:/00_Code/03_VasoTracker/vasotracker2.0_no_venv/images/vt_icon.ico',
    # Ensure it's set to True to create a one-file bundled executable
    onefile=True
)

# The COLLECT function is omitted for onefile builds, as everything is packed into the EXE