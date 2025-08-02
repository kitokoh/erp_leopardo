from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Experiencemedia(Base):
    __tablename__ = 'experience_media'
    experience_media_id = Column(Integer, primary_key=True, autoincrement=True)
    experience_id = Column(Text, nullable=False)
    media_item_id = Column(Text, nullable=False)
    created_at = Column(DateTime)


    def __repr__(self):
        return f'<Experiencemedia experience_media_id={self.experience_media_id}>'
