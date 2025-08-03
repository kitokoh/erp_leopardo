from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class AssetAssignment(Base):
    __tablename__ = 'asset_assignments'

    assignment_id = Column(String, primary_key=True)
    asset_id = Column(Text, ForeignKey('company_assets.asset_id'), nullable=False)
    personnel_id = Column(Integer, ForeignKey('company_personnel.personnel_id'), nullable=False)
    assignment_date = Column(DateTime)
    expected_return_date = Column(DateTime)
    actual_return_date = Column(DateTime)
    assignment_status = Column(String)
    notes = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<AssetAssignment(assignment_id='{self.assignment_id}')>"
