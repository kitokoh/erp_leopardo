from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Experiences(Base):
    __tablename__ = 'experiences'
    experience_id = Column(Text, primary_key=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    experience_date = Column(Date)
    type = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    user_id = Column(Text)


    def __repr__(self):
        return f'<Experiences experience_id={self.experience_id}>'
