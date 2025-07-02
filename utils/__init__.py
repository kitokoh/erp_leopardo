# This file makes the 'utils' directory a Python package.

# Import functions from auth.py to make them accessible
# directly from the 'utils' package.
from .auth import hash_password, verify_password
from .docx import populate_docx_template
from .config import (
    get_config_dir,
    get_config_file_path,
    load_config,
    save_config,
    is_first_launch,
    mark_initial_setup_complete
)
from .pdf import generate_pdf_for_document

# Make them available for wildcard import if desired, though explicit is better.
__all__ = [
    'hash_password', 'verify_password',
    'populate_docx_template',
    'get_config_dir', 'get_config_file_path', 'load_config', 'save_config',
    'is_first_launch', 'mark_initial_setup_complete',
    'generate_pdf_for_document'
]

