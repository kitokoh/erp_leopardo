from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Candidateprogress(Base):
    __tablename__ = 'candidate_progress'
    candidate_progress_id = Column(Text, primary_key=True)
    candidate_id = Column(Text, nullable=False, ForeignKey('candidates.candidate_id'))

    recruitment_step_id = Column(Text, nullable=False, ForeignKey('recruitmentsteps.recruitment_step_id'))

    status_id = Column(Integer, ForeignKey('statussettings.status_id'))

    notes = Column(Text)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime)


    def __repr__(self):
        return f'<Candidateprogress candidate_progress_id={self.candidate_progress_id}>'
    candidate_rel = relationship('Candidates')
    recruitmentstep_rel = relationship('Recruitmentsteps')
    statussetting_rel = relationship('Statussettings')
