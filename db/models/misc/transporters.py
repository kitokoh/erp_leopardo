from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Transporters(Base):
    __tablename__ = 'transporters'
    transporter_id = Column(Text, primary_key=True, nullable=False)
    phone = Column(Text)
    latitude = Column(REAL)
    longitude = Column(REAL)
    current_cargo = Column(Text)
    created_at = Column(DateTime)


    def __repr__(self):
        return f'<Transporters transporter_id={self.transporter_id}>'
