from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class RecruitmentStep(Base):
    __tablename__ = 'recruitment_steps'

    recruitment_step_id = Column(String, primary_key=True)
    job_opening_id = Column(Text, ForeignKey('job_openings.job_opening_id'), nullable=False)
    step_name = Column(String)
    step_order = Column(Integer)
    description = Column(Text)

    def __repr__(self):
        return f"<RecruitmentStep(recruitment_step_id='{self.recruitment_step_id}')>"
