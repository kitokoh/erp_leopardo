from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Interviews(Base):
    __tablename__ = 'interviews'
    interview_id = Column(Text, primary_key=True)
    candidate_id = Column(Text, nullable=False, ForeignKey('candidates.candidate_id'))

    job_opening_id = Column(Text, nullable=False, ForeignKey('jobopenings.job_opening_id'))

    recruitment_step_id = Column(Text, ForeignKey('recruitmentsteps.recruitment_step_id'))

    interviewer_team_member_id = Column(Integer, ForeignKey('teammembers.team_member_id'))

    scheduled_at = Column(DateTime)
    duration_minutes = Column(Integer)
    interview_type = Column(Text)
    location_or_link = Column(Text)
    status_id = Column(Integer, ForeignKey('statussettings.status_id'))

    feedback_notes_overall = Column(Text)
    feedback_rating = Column(Integer)
    created_by_user_id = Column(Text, ForeignKey('users.user_id'))

    created_at = Column(DateTime)
    updated_at = Column(DateTime)


    def __repr__(self):
        return f'<Interviews interview_id={self.interview_id}>'
    candidate_rel = relationship('Candidates')
    jobopening_rel = relationship('Jobopenings')
    recruitmentstep_rel = relationship('Recruitmentsteps')
    teammember_rel = relationship('Teammembers')
    statussetting_rel = relationship('Statussettings')
    user_rel = relationship('Users')
