from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Partners(Base):
    __tablename__ = 'partners'
    partner_id = Column(Text, primary_key=True, nullable=False)
    contact_person_name = Column(Text, unique=True)
    website_url = Column(Text)
    status = Column(Text)
    created_at = Column(Text, nullable=False)


    def __repr__(self):
        return f'<Partners partner_id={self.partner_id}>'
    partnercategorie_rel = relationship('Partnercategories')
