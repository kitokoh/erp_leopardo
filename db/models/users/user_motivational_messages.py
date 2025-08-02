from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class UserMotivationalMessages(Base):
    __tablename__ = 'user_motivational_messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    message = Column(Text, nullable=False)
    language_code = Column(Text)
    is_active = Column(Boolean)
    -- = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


    def __repr__(self):
        return f'<UserMotivationalMessages id={self.id}>'
