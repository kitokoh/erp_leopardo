from sqlalchemy import Column, Text, DateTime, ForeignKey, REAL
from sqlalchemy.orm import relationship
from db.connection import Base

class ProductStorageLocation(Base):
    __tablename__ = 'product_storage_locations'

    product_storage_location_id = Column(Text, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.product_id'), nullable=False)
    location_id = Column(Text, ForeignKey('item_locations.location_id'), nullable=False)
    quantity_at_location = Column(REAL)
    last_updated = Column(DateTime)

    product = relationship("Product")
    location = relationship("ItemLocation")

    def __repr__(self):
        return f'<ProductStorageLocation id={self.product_storage_location_id}>'
