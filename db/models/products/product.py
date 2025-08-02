from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Product(Base):
    __tablename__ = 'products'

    product_id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)
    language_code = Column(String, default='fr', nullable=False)
    base_unit_price = Column(Float, nullable=False)
    unit_of_measure = Column(String, nullable=True)
    weight = Column(Float, nullable=True)
    dimensions = Column(Text, nullable=True) # Using Text for dimensions
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Integer, default=0, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Product(id='{self.product_id}', product_name='{self.product_name}')>"
