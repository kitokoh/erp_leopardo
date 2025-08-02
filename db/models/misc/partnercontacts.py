from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Partnercontacts(Base):
    __tablename__ = 'partner_contacts'
    partner_contact_id = Column(Integer, primary_key=True, autoincrement=True)
    partner_id = Column(Text, nullable=False)
    contact_id = Column(Integer, nullable=False)
    is_primary = Column(Boolean)
    can_receive_documents = Column(Boolean)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


    def __repr__(self):
        return f'<Partnercontacts partner_contact_id={self.partner_contact_id}>'
