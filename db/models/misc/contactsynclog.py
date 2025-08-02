from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Contactsynclog(Base):
    __tablename__ = 'contact_sync_log'
    sync_log_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    local_contact_id = Column(Text, nullable=False)
    google_contact_id = Column(Text, nullable=False)
    last_sync_timestamp = Column(DateTime, nullable=False)
    sync_direction = Column(Text)
    created_at = Column(DateTime)


    def __repr__(self):
        return f'<Contactsynclog sync_log_id={self.sync_log_id}>'
