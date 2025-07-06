# -*- coding: utf-8 -*-
import os
# import json # Moved with config functions
import sys
import logging # Added logging
# from datetime import datetime # Moved with generate_pdf_for_document

# QStandardPaths moved with config functions
# QUrl moved with generate_pdf_for_document
# QDesktopServices moved with generate_pdf_for_document (assuming it was for it)
from PyQt5.QtCore import QCoreApplication # Retained for potential remaining Qt utilities, or if QMessageBox needs it implicitly
from PyQt5.QtWidgets import QMessageBox # Retained for potential remaining Qt utilities



# MAIN_APP_ROOT_DIR related comments are now with the functions that used it.

# Configuration constants and functions have been moved to utils/config.py

# --- DOCX Population Logic ---
# This function has been moved to utils/docx.py

# --- PDF Generation Logic ---
# This function has been moved to utils/pdf.py

# Note: APP_ROOT_DIR comments moved with generate_pdf_for_document to utils/pdf.py (or considered as part of its context).

# --- Password Hashing Utilities ---
# These functions have been moved to utils/auth.py

def sanitize_foldername(name_part: str) -> str:
    """
    Sanitizes a string to be safe for use as a folder name component.
    Removes or replaces characters invalid for Windows and common OS folder names.
    Also handles leading/trailing spaces/periods and empty names.
    """
    if not name_part:
        return "sanitized_empty_name" # Or handle as error upstream

    name_part = str(name_part) # Ensure it's a string

    # Characters invalid in Windows folder names (and often other OSes)
    # Includes: < > : " / \ | ? *
    # Also, control characters (0-31) are problematic.
    # Using a raw string for the backslash
    invalid_filename_chars_str = r'<>:"/\|?*'
    invalid_filename_chars = list(invalid_filename_chars_str)

    for char_code in range(32): # ASCII 0-31
        invalid_filename_chars.append(chr(char_code))

    for char in invalid_filename_chars:
        name_part = name_part.replace(char, '_')

    # Replace multiple consecutive underscores (optional, for aesthetics)
    import re
    name_part = re.sub(r'_{2,}', '_', name_part)

    # Names cannot end with a space or period on Windows.
    # Also, strip leading/trailing whitespace generally.
    name_part = name_part.strip(' .') # Strip leading/trailing spaces and periods

    # If the name becomes empty after sanitization, provide a default.
    if not name_part:
        return "sanitized_empty_name_after_strip" # Or a more specific default

    # Limit length (optional, but good for cross-platform compatibility)
    # MAX_COMPONENT_LENGTH = 255 # A common limit, but complex with full paths
    # name_part = name_part[:MAX_COMPONENT_LENGTH]

    return name_part
