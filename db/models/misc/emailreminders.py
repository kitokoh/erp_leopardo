from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Emailreminders(Base):
    __tablename__ = 'email_reminders'
    reminder_id = Column(Integer, primary_key=True, autoincrement=True)
    scheduled_email_id = Column(Integer, nullable=False, ForeignKey('scheduledemails.scheduled_email_id'))

    reminder_type = Column(Text, nullable=False)
    reminder_send_at = Column(DateTime, nullable=False)
    status = Column(Text, nullable=False)
    created_at = Column(DateTime)


    def __repr__(self):
        return f'<Emailreminders reminder_id={self.reminder_id}>'
    scheduledemail_rel = relationship('Scheduledemails')
