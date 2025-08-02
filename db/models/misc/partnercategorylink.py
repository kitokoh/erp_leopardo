from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Partnercategorylink(Base):
    __tablename__ = 'partner_category_link'
    partner_id = Column(Text, nullable=False)


    def __repr__(self):
        return f'<Partnercategorylink partner_id={self.partner_id}>'
