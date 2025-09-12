from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base

class Region(Base):
    __tablename__ = 'regions'

    region_id = Column(Integer, primary_key=True, autoincrement=True)
    region_name = Column(String)
    country_id = Column(Integer, ForeignKey('countries.country_id'), nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<Region(region_id='{self.region_id}')>"
