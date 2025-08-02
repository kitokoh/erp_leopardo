from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Companypersonnelcontacts(Base):
    __tablename__ = 'company_personnel_contacts'
    company_personnel_contact_id = Column(Integer, primary_key=True, autoincrement=True)
    personnel_id = Column(Integer, nullable=False)
    contact_id = Column(Integer, nullable=False)
    is_primary = Column(Boolean)
    can_receive_documents = Column(Boolean)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


    def __repr__(self):
        return f'<Companypersonnelcontacts company_personnel_contact_id={self.company_personnel_contact_id}>'
