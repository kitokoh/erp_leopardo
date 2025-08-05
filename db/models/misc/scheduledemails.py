from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class ScheduledEmail(Base):
    __tablename__ = 'scheduled_emails'

    scheduled_email_id = Column(Integer, primary_key=True, autoincrement=True)
    recipient_email = Column(String)
    subject = Column(String)
    body_html = Column(Text)
    body_text = Column(Text)
    scheduled_send_at = Column(DateTime)
    status = Column(String)
    sent_at = Column(DateTime)
    error_message = Column(Text)
    related_client_id = Column(String, ForeignKey('clients.client_id'))
    related_project_id = Column(String, ForeignKey('projects.project_id'))
    created_by_user_id = Column(String, ForeignKey('users.user_id'))
    created_at = Column(DateTime)

    def __repr__(self):
        return f"<ScheduledEmail(scheduled_email_id='{self.scheduled_email_id}')>"
