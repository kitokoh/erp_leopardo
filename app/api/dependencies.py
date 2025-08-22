# This file contains dependencies for the FastAPI routers,
# such as getting a database session.
from app.db.connection import SessionLocal

def get_db_session():
    """
    FastAPI dependency that provides a SQLAlchemy database session.
    """
    db = None
    try:
        db = SessionLocal()
        yield db
    finally:
        if db:
            db.close()
