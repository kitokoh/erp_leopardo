from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class CompanyPersonnel(Base):
    __tablename__ = 'company_personnel'

    personnel_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Text, ForeignKey('companies.company_id'), nullable=False)
    name = Column(String)
    role = Column(String)
    phone = Column(String)
    email = Column(String)
    created_at = Column(DateTime)

    def __repr__(self):
        return f"<CompanyPersonnel(personnel_id='{self.personnel_id}')>"
