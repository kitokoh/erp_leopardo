from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Scheduledemails(Base):
    __tablename__ = 'scheduled_emails'
    scheduled_email_id = Column(Integer, primary_key=True, autoincrement=True)
    recipient_email = Column(Text, nullable=False)
    subject = Column(Text, nullable=False)
    body_html = Column(Text)
    body_text = Column(Text)
    scheduled_send_at = Column(DateTime, nullable=False)
    status = Column(Text, nullable=False)
    sent_at = Column(DateTime)
    error_message = Column(Text)
    related_client_id = Column(Text, ForeignKey('clients.client_id'))

    related_project_id = Column(Text, ForeignKey('projects.project_id'))

    created_by_user_id = Column(Text, ForeignKey('users.user_id'))

    created_at = Column(DateTime)


    def __repr__(self):
        return f'<Scheduledemails scheduled_email_id={self.scheduled_email_id}>'
    client_rel = relationship('Clients')
    project_rel = relationship('Projects')
    user_rel = relationship('Users')
