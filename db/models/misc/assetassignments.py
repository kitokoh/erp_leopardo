from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Assetassignments(Base):
    __tablename__ = 'asset_assignments'
    assignment_id = Column(Text, primary_key=True)
    asset_id = Column(Text, nullable=False, ForeignKey('companyassets.asset_id'))

    personnel_id = Column(Integer, nullable=False, ForeignKey('companypersonnel.personnel_id'))

    assignment_date = Column(DateTime, nullable=False)
    expected_return_date = Column(DateTime)
    actual_return_date = Column(DateTime)
    assignment_status = Column(Text, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


    def __repr__(self):
        return f'<Assetassignments assignment_id={self.assignment_id}>'
    companyasset_rel = relationship('Companyassets')
    companypersonne_rel = relationship('Companypersonnel')
