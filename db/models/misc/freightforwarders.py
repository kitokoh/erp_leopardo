from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Freightforwarders(Base):
    __tablename__ = 'freight_forwarders'
    forwarder_id = Column(Text, primary_key=True, nullable=False)
    phone = Column(Text)
    created_at = Column(DateTime)


    def __repr__(self):
        return f'<Freightforwarders forwarder_id={self.forwarder_id}>'
