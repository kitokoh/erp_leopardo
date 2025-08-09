from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class ItemLocation(Base):
    __tablename__ = 'item_locations'
    location_id = Column(Text, primary_key=True)
    location_name = Column(Text)
    location_type = Column(Text)
    parent_location_id = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


    def __repr__(self):
        return f'<Itemlocations location_id={self.location_id}>'
