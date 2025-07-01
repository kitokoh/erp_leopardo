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

# Document import was removed earlier.
# import db as db_manager # Moved with generate_pdf_for_document
# from html_to_pdf_util import convert_html_to_pdf # Moved with generate_pdf_for_document

# MAIN_APP_ROOT_DIR related comments are now with the functions that used it.

# Configuration constants and functions have been moved to utils/config.py

# --- DOCX Population Logic ---
# This function has been moved to utils/docx.py

# --- PDF Generation Logic ---
# This function has been moved to utils/pdf.py

# Note: APP_ROOT_DIR comments moved with generate_pdf_for_document to utils/pdf.py (or considered as part of its context).

# --- Password Hashing Utilities ---
# These functions have been moved to utils/auth.py

