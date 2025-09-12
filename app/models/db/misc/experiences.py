from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base

class Experience(Base):
    __tablename__ = 'experiences'

    experience_id = Column(String, primary_key=True)
    title = Column(String)
    description = Column(Text)
    experience_date = Column(Date)
    type = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    user_id = Column(String, ForeignKey('users.user_id'))

    def __repr__(self):
        return f"<Experience(experience_id='{self.experience_id}')>"
