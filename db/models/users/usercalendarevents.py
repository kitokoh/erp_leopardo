from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Usercalendarevents(Base):
    __tablename__ = 'user_calendar_events'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, nullable=False, ForeignKey('users.user_id', ForeignKey('users.user_id'))
, ForeignKey('users.user_id'))


    event_date = Column(Date, nullable=False)
    event_type = Column(Text, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


    def __repr__(self):
        return f'<Usercalendarevents id={self.id}>'
    user_rel = relationship('Users')
    user_rel = relationship('Users')
