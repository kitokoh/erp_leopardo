from sqlalchemy import Column, Integer, String
from db.connection import Base

class LeaveType(Base):
    __tablename__ = 'leave_types'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    default_days_entitled = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<LeaveType(id={self.id}, name='{self.name}')>"
