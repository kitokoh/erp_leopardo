import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base
from ..employees.employee import Employee
from .leave_type import LeaveType
from ..users.user import User
from app.api.models import LeaveRequestStatusEnum


class LeaveRequest(Base):
    __tablename__ = 'leave_requests'

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String, ForeignKey('employees.id'), nullable=False, index=True)
    leave_type_id = Column(Integer, ForeignKey('leave_types.id'), nullable=False, index=True)
    status = Column(SQLAlchemyEnum(LeaveRequestStatusEnum), nullable=False, default=LeaveRequestStatusEnum.PENDING, index=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=True)
    num_days = Column(Float, nullable=False)
    request_date = Column(DateTime, server_default=func.now(), nullable=False)
    approved_by_id = Column(String, ForeignKey('users.user_id'), nullable=True)
    processed_date = Column(DateTime, nullable=True)
    comments = Column(Text, nullable=True)

    employee = relationship("Employee")
    leave_type = relationship("LeaveType")
    approved_by = relationship("User")

    def __repr__(self):
        return f"<LeaveRequest(id={self.id}, employee_id='{self.employee_id}', status='{self.status.value if self.status else None}')>"
