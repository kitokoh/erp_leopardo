from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Companyassets(Base):
    __tablename__ = 'company_assets'
    asset_id = Column(Text, primary_key=True)
    asset_name = Column(Text, nullable=False)
    asset_type = Column(Text, nullable=False)
    serial_number = Column(Text, unique=True)
    description = Column(Text)
    purchase_date = Column(Date)
    purchase_value = Column(REAL)
    current_status = Column(Text, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    is_deleted = Column(Integer)
    deleted_at = Column(DateTime)


    def __repr__(self):
        return f'<Companyassets asset_id={self.asset_id}>'
