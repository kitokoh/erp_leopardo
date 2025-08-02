from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Productstoragelocations(Base):
    __tablename__ = 'product_storage_locations'
    product_storage_location_id = Column(Text, primary_key=True)
    product_id = Column(Integer)
    location_id = Column(Text)
    quantity_at_location = Column(REAL)
    last_updated = Column(DateTime)


    def __repr__(self):
        return f'<Productstoragelocations product_storage_location_id={self.product_storage_location_id}>'
