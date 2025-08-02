from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Candidates(Base):
    __tablename__ = 'candidates'
    candidate_id = Column(Text, primary_key=True)
    job_opening_id = Column(Text, nullable=False, ForeignKey('jobopenings.job_opening_id'))

    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)
    email = Column(Text, nullable=False, unique=True)
    phone = Column(Text)
    resume_path = Column(Text)
    cover_letter_path = Column(Text)
    application_source = Column(Text)
    current_status_id = Column(Integer, ForeignKey('statussettings.status_id'))

    application_date = Column(DateTime)
    notes = Column(Text)
    linked_contact_id = Column(Integer, ForeignKey('contacts.contact_id'))



    def __repr__(self):
        return f'<Candidates candidate_id={self.candidate_id}>'
    jobopening_rel = relationship('Jobopenings')
    statussetting_rel = relationship('Statussettings')
    contact_rel = relationship('Contacts')
