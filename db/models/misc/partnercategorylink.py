from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class PartnerCategoryLink(Base):
    __tablename__ = 'partner_category_link'

    partner_id = Column(Text, ForeignKey('partners.partner_id'), primary_key=True)
    partner_category_id = Column(Integer, ForeignKey('partner_categories.partner_category_id'), primary_key=True)

    def __repr__(self):
        return f"<PartnerCategoryLink(partner_id='{self.partner_id}', partner_category_id='{self.partner_category_id}')>"
