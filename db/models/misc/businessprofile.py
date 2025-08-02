from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class BusinessProfile(Base):
    __tablename__ = 'business_profile'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    name = Column(String)
    business_type = Column(String)
    sector_id = Column(Integer, ForeignKey('sectors.id'))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<BusinessProfile(id='{self.id}')>"
