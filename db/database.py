from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add project root to sys.path to allow importing config
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from config import DATABASE_PATH
except ImportError:
    # Fallback or error handling if config.py is not found
    # This should ideally not happen if project structure is correct
    # For now, using a default relative path for SQLite if config fails
    print("Error: Could not import DATABASE_PATH from config. Using default 'app_data.db'")
    DATABASE_PATH = "app_data.db"


SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
# For PostgreSQL, it would be:
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # connect_args are specific to SQLite for enabling check_same_thread
    # For other databases, these connect_args might not be needed or different
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Function to create all tables in the database
# This should be called once when the application starts or during setup.
def create_db_and_tables():
    # Import all modules here that define models so that
    # Base has them registered before create_all is called.
    # Example:
    # from accounting import models as accounting_models # if they use this Base
    # from api import models as api_models # if they use this Base
    # Base.metadata.create_all(bind=engine)
    # For now, we'll assume init_schema.py handles SQLite table creation separately
    # or that ORM models will be defined and registered with this Base later.
    print(f"SQLAlchemy engine created for {SQLALCHEMY_DATABASE_URL}. Tables should be created by models inheriting from Base.")

# If you have ORM models defined elsewhere that use this Base,
# ensure they are imported before create_db_and_tables is called,
# or modify create_db_and_tables to import them.
# For example, if your Pydantic models in api.models also have corresponding SQLAlchemy ORM models:
# import api.models # This would trigger their definition if they inherit from Base
# Base.metadata.create_all(bind=engine) # Then create tables
