from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class PartnerContact(Base):
    __tablename__ = 'partner_contacts'

    partner_contact_id = Column(Integer, primary_key=True, autoincrement=True)
    partner_id = Column(String, ForeignKey('partners.partner_id'))
    contact_id = Column(Integer, ForeignKey('contacts.contact_id'))
    is_primary = Column(Boolean)
    can_receive_documents = Column(Boolean)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<PartnerContact(partner_contact_id='{self.partner_contact_id}')>"
