from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class ClientorderMoneytransferagents(Base):
    __tablename__ = 'client_order__money_transfer_agents'
    assignment_id = Column(Text, primary_key=True)
    client_id = Column(Text, nullable=False, ForeignKey('clients.client_id'))

    order_id = Column(Text, ForeignKey('projects.project_id'))

    agent_id = Column(Text, nullable=False, ForeignKey('moneytransferagents.agent_id'))

    assignment_details = Column(Text)
    fee_estimate = Column(REAL)
    assigned_at = Column(Text, nullable=False)
    updated_at = Column(Text)
    email_status = Column(Text)
    is_deleted = Column(Integer)
    deleted_at = Column(Text)


    def __repr__(self):
        return f'<ClientorderMoneytransferagents assignment_id={self.assignment_id}>'
    client_rel = relationship('Clients')
    project_rel = relationship('Projects')
    moneytransferagent_rel = relationship('Moneytransferagents')
