from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class ClientAssignedpersonnel(Base):
    __tablename__ = 'client__assigned_personnel'
    assignment_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    personnel_id = Column(Integer, nullable=False, ForeignKey('companypersonnel.personnel_id'))

    assigned_at = Column(DateTime)


    def __repr__(self):
        return f'<ClientAssignedpersonnel assignment_id={self.assignment_id}>'
    client_rel = relationship('Clients')
    companypersonne_rel = relationship('Companypersonnel')
