# ============================================================
# PyInstaller Build Spec
# Build standalone EXE with: pyinstaller build.spec
# ============================================================
# pip install pyinstaller first

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect mediapipe data files
mediapipe_datas = collect_data_files("mediapipe")
fer_datas = collect_data_files("fer")

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("configs/config.yaml", "configs"),
        ("assets/overlays", "assets/overlays"),
        *mediapipe_datas,
        *fer_datas,
    ],
    hiddenimports=[
        "mediapipe",
        "cv2",
        "numpy",
        "tensorflow",
        "fer",
        "pandas",
        "matplotlib",
        "sqlite3",
        "yaml",
        "loguru",
        *collect_submodules("mediapipe"),
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter"],
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
    name="AI_Emotion_Overlay",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set False to hide console window
    icon="assets/icon.ico",  # Optional: add your icon
)
