from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Partnercategories(Base):
    __tablename__ = 'partner_categories'
    partner_category_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    description = Column(Text, nullable=False)
    updated_at = Column(Text, nullable=False)


    def __repr__(self):
        return f'<Partnercategories partner_category_id={self.partner_category_id}>'
