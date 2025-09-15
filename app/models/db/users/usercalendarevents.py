from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base

class Usercalendarevents(Base):
    __tablename__ = 'user_calendar_events'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, ForeignKey('users.user_id'), nullable=False)
    event_date = Column(Date, nullable=False)
    event_type = Column(Text, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    user_rel = relationship('User')

    def __repr__(self):
        return f'<Usercalendarevents id={self.id}>'
