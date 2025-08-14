import os

# --- Application Information ---
APP_NAME = "Leopardo AI"
APP_VERSION = "2.0.0"  # Modernized version
COMPANY_NAME = "Leopardo, Inc."
APP_ICON = "app/resources/icons/nova360.ico"
MAIN_SCRIPT = "main.py" # Entry script is relative to the app folder

# --- Build Directories ---
BUILD_DIR = "build"
DIST_DIR = "dist"
OBFUSCATED_SRC_DIR = os.path.join(BUILD_DIR, "obfuscated_src")
INSTALLER_DIR = os.path.join(DIST_DIR, "installer")

# --- PyInstaller Configuration ---
SPEC_FILE = "app/compilation/main.spec"
UPX_DIR = "/usr/local/bin/upx" # Example path, may need adjustment

# --- Inno Setup Configuration ---
ISS_FILE = "app/compilation/main.iss"
LICENSE_FILE = "app/compilation/license.txt" # Assuming license file exists
INFO_BEFORE_FILE = "app/compilation/before_install.txt"
INFO_AFTER_FILE = "app/compilation/after_install.txt"

# --- Obfuscation Configuration ---
OBFUSCATION_SCRIPT = "app/compilation/obfuscation.py"
OBFUSCATION_LEVEL = 2 # 1, 2, or 3

# --- Code Signing ---
SIGNING_CERTIFICATE = "" # Path to .pfx file
SIGNING_PASSWORD = "" # Password for the certificate
