from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class MotivationalMessages(Base):
    __tablename__ = 'motivational_messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    language_code = Column(Text, nullable=False)
    message = Column(Text, nullable=False)
    day_of_year = Column(Integer)
    is_active = Column(Boolean)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


    def __repr__(self):
        return f'<MotivationalMessages id={self.id}>'
