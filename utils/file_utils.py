# utils/file_utils.py
import os
from pathlib import Path
import logging

def get_document_full_path(app_config: dict, client_default_base_folder: str, relative_file_path: str, file_name_on_disk: str) -> str:
    """
    Constructs the full absolute path for a document.

    Args:
        app_config (dict): The application configuration dictionary.
                           Expected to have a 'clients_dir' key.
        client_default_base_folder (str): The client-specific base folder path.
                                          This is typically relative to 'clients_dir' or an absolute path
                                          if 'clients_dir' is not used in its construction.
                                          However, current implementation assumes it's a sub-path under clients_dir.
        relative_file_path (str): The path of the file relative to the client's base folder
                                  (e.g., project_identifier or other subfolders).
        file_name_on_disk (str): The actual name of the file.

    Returns:
        str: The absolute path to the document.
    """
    if not app_config:
        logging.error("get_document_full_path: app_config is missing.")
        return "" # Or raise error

    clients_base_dir = app_config.get('clients_dir')
    if not clients_base_dir:
        logging.error("get_document_full_path: 'clients_dir' is missing from app_config.")
        return "" # Or raise error

    # Ensure all path components are strings and not None
    # Pathlib handles joining robustly. We need to ensure no None gets passed to Path() constructor directly if it's the first element
    # and that subsequent elements are not None before appending.

    if not file_name_on_disk: # A file name is essential.
        logging.error("get_document_full_path: file_name_on_disk is missing.")
        return ""

    try:
        # Start with the absolute base directory for all clients
        current_path = Path(clients_base_dir)

        # Append client-specific base folder, if provided
        if client_default_base_folder:
            current_path = current_path / client_default_base_folder

        # Append relative path within the client's folder, if provided
        if relative_file_path:
            current_path = current_path / relative_file_path

        # Finally, append the filename
        current_path = current_path / file_name_on_disk

        # Resolve to get an absolute path and normalize (e.g., '..' components)
        # Use str() to return a string path as per type hint and common usage.
        resolved_path = str(current_path.resolve())
        logging.debug(f"Constructed path: {resolved_path} from components: clients_base_dir='{clients_base_dir}', client_default_base_folder='{client_default_base_folder}', relative_file_path='{relative_file_path}', file_name_on_disk='{file_name_on_disk}'")
        return resolved_path

    except TypeError as e:
        # This might happen if a path component is not a string or Path-like object
        logging.error(f"TypeError during path construction: {e}. Components: clients_base_dir='{clients_base_dir}', client_default_base_folder='{client_default_base_folder}', relative_file_path='{relative_file_path}', file_name_on_disk='{file_name_on_disk}'")
        return ""
    except Exception as e:
        # Catch any other unexpected errors during path construction
        logging.error(f"Unexpected error during path construction: {e}. Components: clients_base_dir='{clients_base_dir}', client_default_base_folder='{client_default_base_folder}', relative_file_path='{relative_file_path}', file_name_on_disk='{file_name_on_disk}'", exc_info=True)
        return ""
