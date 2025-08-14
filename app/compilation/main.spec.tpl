# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files
import os

# This is a template file. The build script will replace placeholders.
# All paths here are expected to be absolute paths provided by the build script.

a = Analysis(
    ['__entry_script__'],
    pathex=['__source_path__', '__project_root__'],
    binaries=[],
    datas=[
        ('__resources_path__/icons', 'resources/icons'),
        ('__resources_path__/gifs', 'resources/gifs'),
        ('__resources_path__/gifshome', 'resources/gifshome'),
        ('__resources_path__/styles', 'resources/styles'),
        ('__resources_path__/templates', 'resources/templates'),
        ('__seed_data_path__', 'db/seed_data'),
        ('__app_dir__/html_editor_assets', 'html_editor_assets'),
        *collect_data_files('PyQt5', subdir='Qt5/translations', include_py_files=False)
    ],
    hiddenimports=[
        'sip', 'pymysql', 'pysqlite2', 'MySQLdb', 'psycopg2', 'ssl',
        'PyQt5.QtWebEngineWidgets', 'cryptography', 'smtplib',
        'email.mime.multipart', 'email.mime.text', 'email.mime.base', 'email.encoders',
        'sqlalchemy.dialects.mysql', 'sqlalchemy.dialects.postgresql', 'sqlalchemy.dialects.sqlite'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='__app_name__',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='__app_icon__',
    distpath='__dist_dir__',
    workpath='__build_dir__'
)