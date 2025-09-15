from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base

class SavTicket(Base):
    __tablename__ = 'sav_tickets'

    ticket_id = Column(String, primary_key=True)
    client_id = Column(String, ForeignKey('clients.client_id'))
    client_project_product_id = Column(Integer, ForeignKey('client_project_products.client_project_product_id'), nullable=False)
    issue_description = Column(Text)
    status_id = Column(Integer, ForeignKey('status_settings.status_id'))
    assigned_technician_id = Column(Integer, ForeignKey('team_members.team_member_id'))
    resolution_details = Column(Text)
    opened_at = Column(DateTime)
    closed_at = Column(DateTime)
    created_by_user_id = Column(String, ForeignKey('users.user_id'))

    def __repr__(self):
        return f"<SavTicket(ticket_id='{self.ticket_id}')>"
