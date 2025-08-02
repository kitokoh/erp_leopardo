from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Experiencetags(Base):
    __tablename__ = 'experience_tags'
    experience_tag_id = Column(Integer, primary_key=True, autoincrement=True)
    experience_id = Column(Text, nullable=False)
    tag_id = Column(Integer, nullable=False)
    created_at = Column(DateTime)


    def __repr__(self):
        return f'<Experiencetags experience_tag_id={self.experience_tag_id}>'
