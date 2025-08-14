import sqlite3
import os
import sys  # Keep sys import for path manipulation
import json
import sys # Import sys
from datetime import datetime
import logging # Keep logging import
import shutil

# --- Configuration Import ---
# Assuming main.py or the entry script handles adding project root to sys.path
try:
    from app import config # This should now find config.py at the root if sys.path is correct
    db_config = config # Alias config as db_config for compatibility
except ImportError as e:
    logging.critical(f"CRITICAL: config.py not found. Ensure project root is in sys.path. Error: {e}")
    raise ImportError(f"config.py is essential and was not found.") from e
# --- End Configuration Import ---

# CRUD function imports

    # CRUD imports removed to prevent circular dependencies.
    # Functions requiring CRUD operations will import `db` directly.
    # print("CRUD functions will be imported dynamically in functions that need them.") # Commented out, too noisy

# Ensure document_generator is findable from db/utils.py
# This might require adjusting sys.path if document_generator is not a sibling package or installed.
# Assuming app_dir (project root) is already in sys.path from the top of this file.
try:
    from document_generator.context_builder import get_document_context as _get_enhanced_document_context
except ImportError as e:
    logging.error(f"Failed to import enhanced context builder from document_generator: {e}. Falling back to basic context if any.")
    # Define a fallback or raise error if this is critical
    def _get_enhanced_document_context(*args, **kwargs):
        logging.error("Using STUB _get_enhanced_document_context due to import error.")
        return {"error": "Enhanced context builder not available."}


# get_db_connection moved to db.connection
# from .connection import get_db_connection # Removed top-level import to break circular dependency


def format_currency(amount: float | None, symbol: str = "€", precision: int = 2) -> str:
    # This function is now defined in document_generator.context_builder
    # This version in db.utils can be deprecated or removed if all calls are updated.
    # For now, keeping it to avoid breaking other potential usages, but it's not locale-aware.
    if amount is None: return ""
    try:
        num_amount = float(amount)
        return f"{symbol}{num_amount:,.{precision}f}"
    except (ValueError, TypeError): return str(amount) # Fallback to string representation if not a number

# _get_batch_products_and_equivalents is now primarily handled within document_generator.context_builder.get_document_context
# This version can be deprecated or removed.
def _get_batch_products_and_equivalents(product_ids: list[int], target_language_code: str, conn_passed=None) -> dict:
    logging.warning("_get_batch_products_and_equivalents in db.utils is deprecated. Logic moved to context_builder.")
    # Fallback to a simple behavior or return empty.
    return {pid: {'original': None, 'equivalents': []} for pid in product_ids}


def get_document_context_data(
    client_id: str, company_id: str, target_language_code: str,
    project_id: str = None,
    linked_product_ids_for_doc: list[int] = None,
    document_type: str = None,
    additional_context: dict = None,
    conn_passed: sqlite3.Connection = None,
    app_root_dir: str = None,
    **kwargs
) -> dict:
    """
    Wrapper function to call the enhanced document context builder, passing through any extra arguments.
    """
    logging.info(f"db.utils.get_document_context_data called, forwarding to enhanced context builder. app_root_dir: {app_root_dir}, kwargs: {kwargs}")

    effective_additional_data = additional_context if isinstance(additional_context, dict) else {}
    if linked_product_ids_for_doc:
        effective_additional_data.setdefault('linked_product_ids_for_doc', linked_product_ids_for_doc)

    # Merge kwargs into additional_data, allowing kwargs to override initial additional_context keys if needed
    effective_additional_data.update(kwargs)

    return _get_enhanced_document_context(
        client_id=client_id,
        company_id=company_id,
        language_code=target_language_code,
        project_id=project_id,
        document_type=document_type,
        additional_data=effective_additional_data,
        db_conn=conn_passed,
        app_root_dir=app_root_dir
    )

__all__ = [
    # "get_db_connection", # Moved to db.connection
    "format_currency",
    "get_document_context_data",
    "save_general_document_file",
    "delete_general_document_file",
]


# Function to save a general document file
def save_general_document_file(source_file_path: str, document_type_subfolder: str, language_code: str, target_base_name: str) -> str | None:
    """
    Saves a general document file to the appropriate templates subfolder.

    Args:
        source_file_path (str): The path to the source file to be copied.
        document_type_subfolder (str): The subfolder name for the document type (e.g., 'quotes', 'invoices').
        language_code (str): The language code for the document (e.g., 'en', 'fr').
        target_base_name (str): The base name for the target file (e.g., 'template.docx').

    Returns:
        str | None: The full path to the saved file on success, or None on error.
    """
    from app_config import CONFIG
    try:
        templates_dir = CONFIG.get("templates_dir", "templates")
        target_dir = os.path.join(templates_dir, document_type_subfolder, language_code)
        os.makedirs(target_dir, exist_ok=True)
        target_file_path = os.path.join(target_dir, target_base_name)
        shutil.copy(source_file_path, target_file_path)
        logging.info(f"Successfully saved document: {target_file_path}")
        return target_file_path
    except (IOError, FileNotFoundError) as e:
        logging.error(f"Error saving document file '{source_file_path}' to '{target_base_name}' in '{document_type_subfolder}/{language_code}': {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred in save_general_document_file: {e}")
        return None

# Function to delete a general document file
def delete_general_document_file(document_type_subfolder: str, language_code: str, base_file_name: str) -> bool:
    """
    Deletes a general document file from the appropriate templates subfolder.

    Args:
        document_type_subfolder (str): The subfolder name for the document type.
        language_code (str): The language code for the document.
        base_file_name (str): The base name of the file to delete.

    Returns:
        bool: True if deletion was successful or if the file didn't exist, False on OSError during deletion.
    """
    from app_config import CONFIG
    try:
        templates_dir = CONFIG.get("templates_dir", "templates")
        file_path_to_delete = os.path.join(templates_dir, document_type_subfolder, language_code, base_file_name)

        if not os.path.exists(file_path_to_delete):
            logging.info(f"File not found, no need to delete: {file_path_to_delete}")
            return True  # File doesn't exist, so considered "successfully" deleted in this context

        os.remove(file_path_to_delete)
        logging.info(f"Successfully deleted document: {file_path_to_delete}")
        return True
    except OSError as e:
        logging.error(f"Error deleting document file '{base_file_name}' from '{document_type_subfolder}/{language_code}': {e}")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred in delete_general_document_file: {e}")
        return False

if __name__ == '__main__': # pragma: no cover
    print("db.utils module direct execution (for testing, may require DB setup)")
    # Example calls for testing
    # test_conn = get_db_connection() # This would now use the import from .connection
    # if test_conn:
    #     print("DB connection successful via get_db_connection.")
    #     test_conn.close()
    # else:
    #     print("DB connection failed via get_db_connection.")
    pass
