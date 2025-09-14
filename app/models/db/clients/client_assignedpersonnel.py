from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base

class ClientAssignedpersonnel(Base):
    __tablename__ = 'client__assigned_personnel'
    assignment_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    client_id = Column(String, ForeignKey('clients.client_id'), nullable=False)
    personnel_id = Column(Integer, ForeignKey('company_personnel.personnel_id'), nullable=False)
    assigned_at = Column(DateTime)

    def __repr__(self):
        return f'<ClientAssignedpersonnel assignment_id={self.assignment_id}>'
    client_rel = relationship('Client', back_populates='assigned_personnel')
    companypersonne_rel = relationship('CompanyPersonnel', back_populates='client_assignments')
