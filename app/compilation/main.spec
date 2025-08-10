# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_data_files
import glob

# --- Version Information ---
with open("version.txt", "r") as f:
    APP_VERSION = f.read().strip()

# --- Application Information ---
APP_NAME = "Leopardo AI"
APP_ICON = "nova360.ico"

# --- Paths ---
DLLS_PATH = 'dlls'
RESOURCES_PATH = 'resources'
KEYS_PATH = os.path.join(RESOURCES_PATH, 'lesClesNova360', 'icons', 'exeCle')

# --- Hooks ---
def hook(hook_api):
    # Example hook to include all files from a specific module
    # hook_api.add_data_files('my_module', 'my_module')
    pass

# --- PyInstaller Analysis ---
a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[(os.path.join(DLLS_PATH, '*'), '.')],
    datas=[
        # --- Resources ---
        (os.path.join(RESOURCES_PATH, 'icons', '*.ico'), os.path.join(RESOURCES_PATH, 'icons')),
        (os.path.join(RESOURCES_PATH, 'icons', '*.png'), os.path.join(RESOURCES_PATH, 'icons')),
        (os.path.join(RESOURCES_PATH, 'data', '*.json'), os.path.join(RESOURCES_PATH, 'data')),
        (os.path.join(RESOURCES_PATH, 'images', '*'), os.path.join(RESOURCES_PATH, 'images')),
        (os.path.join(RESOURCES_PATH, 'videos', '*'), os.path.join(RESOURCES_PATH, 'videos')),
        (os.path.join(RESOURCES_PATH, 'sounds', '*'), os.path.join(RESOURCES_PATH, 'sounds')),
        (os.path.join(RESOURCES_PATH, 'gifs', '*'), os.path.join(RESOURCES_PATH, 'gifs')),
        (os.path.join(RESOURCES_PATH, '*.key'), RESOURCES_PATH),
        (os.path.join(RESOURCES_PATH, 'lang', '*'), os.path.join(RESOURCES_PATH, 'lang')),
        (KEYS_PATH, os.path.join(RESOURCES_PATH, 'tools')),

        # --- PyQt5 ---
        *collect_data_files(
            'PyQt5',
            subdir='Qt5/translations/qtwebengine_locales',
            include_py_files=False
        )
    ],
    hiddenimports=[
        'sip',
        'pymysql',
        'pysqlite2',
        'MySQLdb',
        'psycopg2',
        'ssl',
        'PyQt5.QtWebEngineWidgets',
        'cryptography',
        'smtplib',
        'email.mime.multipart',
        'email.mime.text',
        'email.mime.base',
        'email.encoders'
    ],
    hookspath=[hook],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# --- PYZ ---
pyz = PYZ(a.pure)

# --- EXE ---
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=APP_ICON,
    distpath='dist',
    workpath='build',
    onefile=True
)