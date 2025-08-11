from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class EmailReminder(Base):
    __tablename__ = 'email_reminders'

    reminder_id = Column(Integer, primary_key=True, autoincrement=True)
    scheduled_email_id = Column(Integer, ForeignKey('scheduled_emails.scheduled_email_id'), nullable=False)
    reminder_type = Column(String)
    reminder_send_at = Column(DateTime)
    status = Column(String)
    created_at = Column(DateTime)

    def __repr__(self):
        return f"<EmailReminder(reminder_id='{self.reminder_id}')>"
