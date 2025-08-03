from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class MotivationalMessage(Base):
    __tablename__ = 'motivational_messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    language_code = Column(String)
    message = Column(String)
    day_of_year = Column(Integer)
    is_active = Column(Boolean)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<MotivationalMessage(id='{self.id}')>"
