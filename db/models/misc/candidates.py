from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Candidate(Base):
    __tablename__ = 'candidates'

    candidate_id = Column(String, primary_key=True)
    job_opening_id = Column(Text, ForeignKey('job_openings.job_opening_id'), nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    phone = Column(String)
    resume_path = Column(String)
    cover_letter_path = Column(String)
    application_source = Column(String)
    current_status_id = Column(Integer, ForeignKey('status_settings.status_id'))
    application_date = Column(DateTime)
    notes = Column(String)
    linked_contact_id = Column(Integer, ForeignKey('contacts.contact_id'))

    def __repr__(self):
        return f"<Candidate(candidate_id='{self.candidate_id}')>"
