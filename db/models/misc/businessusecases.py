from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Businessusecases(Base):
    __tablename__ = 'business_use_cases'
    id = Column(Integer, primary_key=True, autoincrement=True)
    business_profile_id = Column(Integer, nullable=False)
    use_case_id = Column(Integer, nullable=False)


    def __repr__(self):
        return f'<Businessusecases id={self.id}>'
