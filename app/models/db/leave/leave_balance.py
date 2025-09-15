from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session_manager import Base
from pydantic import BaseModel
from typing import Optional

# Pydantic Models
class LeaveBalanceBase(BaseModel):
    employee_id: str
    leave_type_id: int
    year: int
    entitled_days: float
    used_days: float = 0.0

class LeaveBalanceCreate(LeaveBalanceBase):
    pass

class LeaveBalanceUpdate(BaseModel):
    entitled_days: Optional[float] = None
    used_days: Optional[float] = None

class LeaveBalance(Base):
    __tablename__ = 'leave_balances'

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String, ForeignKey('employees.id'), nullable=False, index=True)
    leave_type_id = Column(Integer, ForeignKey('leave_types.id'), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    entitled_days = Column(Float, nullable=False)
    used_days = Column(Float, nullable=False, default=0.0)

    employee = relationship("Employee")
    leave_type = relationship("LeaveType")

    __table_args__ = (
        UniqueConstraint('employee_id', 'leave_type_id', 'year', name='uq_employee_leave_year'),
    )

    def __repr__(self):
        return f"<LeaveBalance(id={self.id}, employee_id='{self.employee_id}', leave_type_id={self.leave_type_id}, year={self.year})>"
