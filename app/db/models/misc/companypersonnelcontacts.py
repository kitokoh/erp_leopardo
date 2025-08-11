from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class CompanyPersonnelContact(Base):
    __tablename__ = 'company_personnel_contacts'

    company_personnel_contact_id = Column(Integer, primary_key=True, autoincrement=True)
    personnel_id = Column(Integer, ForeignKey('company_personnel.personnel_id'))
    contact_id = Column(Integer, ForeignKey('contacts.contact_id'))
    is_primary = Column(Boolean)
    can_receive_documents = Column(Boolean)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<CompanyPersonnelContact(company_personnel_contact_id='{self.company_personnel_contact_id}')>"
