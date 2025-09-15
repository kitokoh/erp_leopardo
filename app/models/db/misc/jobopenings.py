from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base

class JobOpening(Base):
    __tablename__ = 'job_openings'

    job_opening_id = Column(String, primary_key=True)
    title = Column(String)
    description = Column(Text)
    status_id = Column(Integer, ForeignKey('status_settings.status_id'))
    department_id = Column(Integer)
    created_by_user_id = Column(String, ForeignKey('users.user_id'))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    closing_date = Column(Date)

    def __repr__(self):
        return f"<JobOpening(job_opening_id='{self.job_opening_id}')>"
