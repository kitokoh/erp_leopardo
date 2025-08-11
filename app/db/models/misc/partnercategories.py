from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class PartnerCategory(Base):
    __tablename__ = 'partner_categories'

    partner_category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(String)
    description = Column(Text)
    created_at = Column(String)
    updated_at = Column(String)

    def __repr__(self):
        return f"<PartnerCategory(partner_category_id='{self.partner_category_id}')>"
