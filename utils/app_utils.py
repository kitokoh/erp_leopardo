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

# --- Document Label Translations ---
import json # For loading translation files

_DOC_LABEL_TRANSLATIONS_CACHE = {}
_DOC_LABEL_BASE_PATH = None # Will be set on first use

def get_doc_label(label_key: str, language_code: str, fallback_text: str = "") -> str:
    """
    Retrieves a translated document label for a given key and language.
    Loads translations from JSON files in translations/doc_labels/.
    Caches loaded translations.
    """
    global _DOC_LABEL_TRANSLATIONS_CACHE
    global _DOC_LABEL_BASE_PATH

    if not _DOC_LABEL_BASE_PATH:
        # Determine base path relative to this app_utils.py file
        # app_utils.py is in utils/
        # translations/ is at the project root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir) # Moves from utils/ to project_root/
        _DOC_LABEL_BASE_PATH = os.path.join(project_root, "translations", "doc_labels")
        logging.info(f"Doc label base path set to: {_DOC_LABEL_BASE_PATH}")

    lang_cache = _DOC_LABEL_TRANSLATIONS_CACHE.get(language_code)
    if lang_cache is None:
        # Attempt to load translations for the language
        try:
            # Ensure language_code is sanitized if it comes from user input, though here it's internal
            file_path = os.path.join(_DOC_LABEL_BASE_PATH, f"{language_code.lower()}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    lang_cache = json.load(f)
                _DOC_LABEL_TRANSLATIONS_CACHE[language_code] = lang_cache
                logging.info(f"Loaded document labels for language: {language_code}")
            else:
                logging.warning(f"Translation file not found for language: {language_code} at {file_path}")
                _DOC_LABEL_TRANSLATIONS_CACHE[language_code] = {} # Cache empty dict to avoid re-attempts
                lang_cache = {}
        except Exception as e:
            logging.error(f"Error loading document labels for language {language_code}: {e}", exc_info=True)
            _DOC_LABEL_TRANSLATIONS_CACHE[language_code] = {} # Cache empty on error
            lang_cache = {}

    translation = lang_cache.get(label_key)
    if translation is not None:
        return translation
    else:
        # Fallback if key not found in specific language: try English
        if language_code != 'en':
            logging.warning(f"Label key '{label_key}' not found for language '{language_code}'. Trying 'en'.")
            en_translations = _DOC_LABEL_TRANSLATIONS_CACHE.get('en')
            if en_translations is None: # Load English if not already cached
                try:
                    en_file_path = os.path.join(_DOC_LABEL_BASE_PATH, "en.json")
                    if os.path.exists(en_file_path):
                        with open(en_file_path, 'r', encoding='utf-8') as f:
                            en_translations = json.load(f)
                        _DOC_LABEL_TRANSLATIONS_CACHE['en'] = en_translations
                    else: # Should not happen if en.json is guaranteed
                         _DOC_LABEL_TRANSLATIONS_CACHE['en'] = {}
                         en_translations = {}
                except Exception as e_en:
                    logging.error(f"Error loading English document labels: {e_en}", exc_info=True)
                    _DOC_LABEL_TRANSLATIONS_CACHE['en'] = {}
                    en_translations = {}

            en_translation = en_translations.get(label_key)
            if en_translation is not None:
                return en_translation

        # Final fallback
        logging.warning(f"Label key '{label_key}' not found for language '{language_code}' or 'en'. Using fallback text or key.")
        return fallback_text if fallback_text else label_key


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
