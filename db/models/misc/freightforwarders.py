from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class FreightForwarder(Base):
    __tablename__ = 'freight_forwarders'

    forwarder_id = Column(String, primary_key=True)
    name = Column(String)
    contact_person = Column(String)
    phone = Column(String)
    email = Column(String)
    address = Column(Text)
    services_offered = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<FreightForwarder(forwarder_id='{self.forwarder_id}')>"
