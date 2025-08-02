from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Jobopenings(Base):
    __tablename__ = 'job_openings'
    job_opening_id = Column(Text, primary_key=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    status_id = Column(Integer, ForeignKey('statussettings.status_id'))

    department_id = Column(Integer)
    created_by_user_id = Column(Text, ForeignKey('users.user_id'))

    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    closing_date = Column(Date)
    -- = Column(String)


    def __repr__(self):
        return f'<Jobopenings job_opening_id={self.job_opening_id}>'
    statussetting_rel = relationship('Statussettings')
    user_rel = relationship('Users')
