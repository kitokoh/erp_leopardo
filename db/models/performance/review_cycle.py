from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from db.connection import Base

class ReviewCycle(Base):
    __tablename__ = 'review_cycles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<ReviewCycle(id={self.id}, name='{self.name}')>"
