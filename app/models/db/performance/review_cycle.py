from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.db.session_manager import Base
from pydantic import BaseModel
from typing import Optional
from datetime import date

# Pydantic Models
class ReviewCycleBase(BaseModel):
    name: str
    start_date: date
    end_date: date
    is_active: bool = True

class ReviewCycleCreate(ReviewCycleBase):
    pass

class ReviewCycleUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None

class ReviewCycle(Base):
    __tablename__ = 'review_cycles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<ReviewCycle(id={self.id}, name='{self.name}')>"
