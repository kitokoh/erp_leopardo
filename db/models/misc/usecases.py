from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Usecases(Base):
    __tablename__ = 'use_cases'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


    def __repr__(self):
        return f'<Usecases id={self.id}>'
