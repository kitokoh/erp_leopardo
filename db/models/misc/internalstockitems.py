from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Internalstockitems(Base):
    __tablename__ = 'internal_stock_items'
    item_id = Column(Text, primary_key=True)
    item_name = Column(Text)
    item_code = Column(Text, unique=True)
    category = Column(Text)
    description = Column(Text)
    quantity = Column(REAL)
    unit_of_measure = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


    def __repr__(self):
        return f'<Internalstockitems item_id={self.item_id}>'
