from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Itemstoragelocations(Base):
    __tablename__ = 'item_storage_locations'
    item_storage_location_id = Column(Text, primary_key=True)
    item_id = Column(Text)
    location_id = Column(Text)
    quantity_at_location = Column(REAL)
    last_updated = Column(DateTime)


    def __repr__(self):
        return f'<Itemstoragelocations item_storage_location_id={self.item_storage_location_id}>'
