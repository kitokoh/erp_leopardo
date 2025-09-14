import os

# Expose the connection module and its key components at the package level
from . import connection
from .connection import get_db_connection, initialize_engine_and_session, engine, SessionLocal

# Conditionally import CRUD modules only if not running in Alembic context
# if 'ALEMBIC_VERSION' not in os.environ:
#     from . import cruds

# Define __all__ to control what 'from db import *' imports
__all__ = [
    'connection',
    'get_db_connection',
    'initialize_engine_and_session',
    'engine',
    'SessionLocal',
    # 'cruds' # Add cruds here if you want it to be part of the wildcard import
]
