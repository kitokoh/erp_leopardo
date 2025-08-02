from sqlalchemy.orm import Session
from ..models import Transporter
import logging
from typing import List, Optional, Dict, Any
from uuid import uuid4
from datetime import datetime

class TransportersCRUD:
    def add_transporter(self, db: Session, data: Dict[str, Any]) -> Optional[Transporter]:
        """Adds a new transporter."""
        try:
            new_transporter = Transporter(**data)
            db.add(new_transporter)
            db.commit()
            db.refresh(new_transporter)
            return new_transporter
        except Exception as e:
            db.rollback()
            logging.error(f"Error adding transporter: {e}")
            return None

    def get_transporter_by_id(self, db: Session, transporter_id: str) -> Optional[Transporter]:
        """Retrieves a transporter by its ID."""
        return db.query(Transporter).filter(Transporter.transporter_id == transporter_id).first()

    def get_all_transporters(self, db: Session) -> List[Transporter]:
        """Retrieves all transporters."""
        return db.query(Transporter).order_by(Transporter.name).all()

    def update_transporter(self, db: Session, transporter_id: str, data: Dict[str, Any]) -> bool:
        """Updates a transporter."""
        transporter = self.get_transporter_by_id(db, transporter_id)
        if not transporter or not data:
            return False

        data['updated_at'] = datetime.utcnow()
        for key, value in data.items():
            setattr(transporter, key, value)

        db.commit()
        return True

    def delete_transporter(self, db: Session, transporter_id: str) -> bool:
        """Deletes a transporter."""
        transporter = self.get_transporter_by_id(db, transporter_id)
        if transporter:
            db.delete(transporter)
            db.commit()
            return True
        return False

transporters_crud = TransportersCRUD()
