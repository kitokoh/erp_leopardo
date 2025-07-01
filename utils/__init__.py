# This file makes the 'utils' directory a Python package.

# Import functions from auth.py to make them accessible
# directly from the 'utils' package.
from .auth import hash_password, verify_password
from .docx import populate_docx_template

# Make them available for wildcard import if desired, though explicit is better.
__all__ = ['hash_password', 'verify_password', 'populate_docx_template']

