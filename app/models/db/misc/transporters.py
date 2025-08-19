from sqlalchemy import Column, Integer, String, Text, DateTime, REAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class Transporter(Base):
    __tablename__ = 'transporters'

    transporter_id = Column(String, primary_key=True)
    name = Column(String)
    contact_person = Column(String)
    phone = Column(String)
    email = Column(String)
    address = Column(Text)
    service_area = Column(Text)
    notes = Column(Text)
    latitude = Column(REAL)
    longitude = Column(REAL)
    current_cargo = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<Transporter(transporter_id='{self.transporter_id}')>"
