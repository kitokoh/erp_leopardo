from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, REAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class ProductStorageLocation(Base):
    __tablename__ = 'product_storage_locations'

    product_storage_location_id = Column(String, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.product_id'))
    location_id = Column(String, ForeignKey('item_locations.location_id'))
    quantity_at_location = Column(REAL)
    last_updated = Column(DateTime)

    def __repr__(self):
        return f"<ProductStorageLocation(product_storage_location_id='{self.product_storage_location_id}')>"
