import logging
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DatabaseSessionManager:
    def __init__(self):
        self._engine = None
        self._session_maker = None
        self.db_url = None

    def initialize(self, db_url: str):
        if self.db_url == db_url and self._engine is not None:
            logging.info("Database engine is already initialized with the same URL.")
            return

        self.db_url = db_url
        logging.info(f"Initializing database engine with URL: {self.db_url}")
        self._engine = create_engine(self.db_url, echo=False)
        self._session_maker = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
        logging.info("Database engine and session maker initialized.")

    @contextmanager
    def get_session(self) -> Session:
        """Provide a transactional scope around a series of operations."""
        if self._session_maker is None:
            raise Exception("Session manager has not been initialized. Call initialize() first.")

        session = self._session_maker()
        try:
            yield session
            session.commit()
        except Exception as e:
            logging.error(f"Session rollback due to exception: {e}", exc_info=True)
            session.rollback()
            raise
        finally:
            session.close()

def get_db():
    """
    Dependency for FastAPI to get a database session.
    """
    with session_manager.get_session() as db:
        yield db

# Global instance of the session manager
session_manager = DatabaseSessionManager()
