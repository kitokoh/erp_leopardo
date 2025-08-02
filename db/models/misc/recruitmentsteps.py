from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Recruitmentsteps(Base):
    __tablename__ = 'recruitment_steps'
    recruitment_step_id = Column(Text, primary_key=True)
    job_opening_id = Column(Text, nullable=False, ForeignKey('jobopenings.job_opening_id'))

    step_name = Column(Text, nullable=False)
    step_order = Column(Integer, nullable=False)
    description = Column(Text)


    def __repr__(self):
        return f'<Recruitmentsteps recruitment_step_id={self.recruitment_step_id}>'
    jobopening_rel = relationship('Jobopenings')
