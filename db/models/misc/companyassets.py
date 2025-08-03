from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class CompanyAsset(Base):
    __tablename__ = 'company_assets'

    asset_id = Column(String, primary_key=True)
    asset_name = Column(String)
    asset_type = Column(String)
    serial_number = Column(String)
    description = Column(Text)
    purchase_date = Column(Date)
    purchase_value = Column(REAL)
    current_status = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    is_deleted = Column(Integer)
    deleted_at = Column(DateTime)

    def __repr__(self):
        return f"<CompanyAsset(asset_id='{self.asset_id}')>"
