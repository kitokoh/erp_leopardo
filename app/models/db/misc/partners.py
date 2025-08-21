from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class Partner(Base):
    __tablename__ = 'partners'

    partner_id = Column(String, primary_key=True)
    partner_name = Column(String)
    partner_category_id = Column(Integer, ForeignKey('partner_categories.partner_category_id'))
    contact_person_name = Column(String)
    email = Column(String)
    phone = Column(String)
    address = Column(Text)
    website_url = Column(String)
    services_offered = Column(Text)
    collaboration_start_date = Column(String)
    status = Column(String)
    notes = Column(Text)
    created_at = Column(String)
    updated_at = Column(String)

    def __repr__(self):
        return f"<Partner(partner_id='{self.partner_id}')>"
