from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class ProductDimension(Base):
    __tablename__ = 'product_dimensions'

    product_id = Column(Integer, ForeignKey('products.product_id'), primary_key=True)
    dim_A = Column(String)
    dim_B = Column(String)
    dim_C = Column(String)
    dim_D = Column(String)
    dim_E = Column(String)
    dim_F = Column(String)
    dim_G = Column(String)
    dim_H = Column(String)
    dim_I = Column(String)
    dim_J = Column(String)
    technical_image_path = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<ProductDimension(product_id='{self.product_id}')>"
