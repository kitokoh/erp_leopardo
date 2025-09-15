from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base

class Interview(Base):
    __tablename__ = 'interviews'

    interview_id = Column(String, primary_key=True)
    candidate_id = Column(Text, ForeignKey('candidates.candidate_id'), nullable=False)
    job_opening_id = Column(Text, ForeignKey('job_openings.job_opening_id'), nullable=False)
    recruitment_step_id = Column(Text, ForeignKey('recruitment_steps.recruitment_step_id'))
    interviewer_team_member_id = Column(Integer, ForeignKey('team_members.team_member_id'))
    scheduled_at = Column(DateTime)
    duration_minutes = Column(Integer)
    interview_type = Column(String)
    location_or_link = Column(String)
    status_id = Column(Integer, ForeignKey('status_settings.status_id'))
    feedback_notes_overall = Column(Text)
    feedback_rating = Column(Integer)
    created_by_user_id = Column(String, ForeignKey('users.user_id'))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<Interview(interview_id='{self.interview_id}')>"
