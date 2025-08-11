from sqlalchemy import Column, Integer, String, Text, DateTime, REAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class InternalStockItem(Base):
    __tablename__ = 'internal_stock_items'

    item_id = Column(String, primary_key=True)
    item_name = Column(String)
    item_code = Column(String)
    category = Column(String)
    description = Column(Text)
    quantity = Column(REAL)
    unit_of_measure = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<InternalStockItem(item_id='{self.item_id}')>"
