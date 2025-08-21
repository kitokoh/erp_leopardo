from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class CandidateProgress(Base):
    __tablename__ = 'candidate_progress'

    candidate_progress_id = Column(String, primary_key=True)
    candidate_id = Column(Text, ForeignKey('candidates.candidate_id'), nullable=False)
    recruitment_step_id = Column(Text, ForeignKey('recruitment_steps.recruitment_step_id'), nullable=False)
    status_id = Column(Integer, ForeignKey('status_settings.status_id'))
    notes = Column(String)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<CandidateProgress(candidate_progress_id='{self.candidate_progress_id}')>"
