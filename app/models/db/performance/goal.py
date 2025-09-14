import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class GoalStatusEnum(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# Pydantic Models
class GoalBase(BaseModel):
    employee_id: str
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[GoalStatusEnum] = GoalStatusEnum.OPEN
    set_by_id: Optional[str] = None

class GoalCreate(GoalBase):
    pass

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[GoalStatusEnum] = None

class GoalInDBBase(GoalBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class Goal(Base):
    __tablename__ = 'goals'

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String, ForeignKey('employees.id'), nullable=False, index=True)
    set_by_id = Column(String, ForeignKey('users.user_id'), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    status = Column(SQLAlchemyEnum(GoalStatusEnum), nullable=False, default=GoalStatusEnum.OPEN)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    employee = relationship("Employee")
    set_by = relationship("User")

    def __repr__(self):
        return f"<Goal(id={self.id}, title='{self.title}', employee_id='{self.employee_id}')>"
