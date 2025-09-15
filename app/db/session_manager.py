import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

class DatabaseSessionManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DatabaseSessionManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.engine = None
        self.SessionLocal = None
        self._initialized = True

    def initialize_engine_and_session(self, db_path: str):
        if self.engine is None:
            try:
                db_url = f"sqlite:///{db_path}"
                self.engine = create_engine(db_url, connect_args={"check_same_thread": False})
                self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
                logging.info(f"Database engine and session initialized for path: {db_path}")
            except Exception as e:
                logging.critical(f"Failed to initialize database engine: {e}", exc_info=True)
                raise

    def get_session(self) -> Session:
        if self.SessionLocal is None:
            logging.error("SessionLocal not initialized. Call initialize_engine_and_session first.")
            raise RuntimeError("Database session factory is not initialized.")
        return self.SessionLocal()

    def get_engine(self):
        if self.engine is None:
            logging.error("Engine not initialized. Call initialize_engine_and_session first.")
            raise RuntimeError("Database engine is not initialized.")
        return self.engine

# Singleton instance
session_manager = DatabaseSessionManager()
