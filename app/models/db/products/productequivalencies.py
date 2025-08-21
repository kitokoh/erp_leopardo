from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class ProductEquivalency(Base):
    __tablename__ = 'product_equivalencies'

    equivalence_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id_a = Column(Integer, ForeignKey('products.product_id'), nullable=False)
    product_id_b = Column(Integer, ForeignKey('products.product_id'), nullable=False)

    def __repr__(self):
        return f"<ProductEquivalency(equivalence_id='{self.equivalence_id}')>"
