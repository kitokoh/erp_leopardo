from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class ExperienceTag(Base):
    __tablename__ = 'experience_tags'

    experience_tag_id = Column(Integer, primary_key=True, autoincrement=True)
    experience_id = Column(String, ForeignKey('experiences.experience_id'))
    tag_id = Column(Integer, ForeignKey('tags.tag_id'))
    created_at = Column(DateTime)

    def __repr__(self):
        return f"<ExperienceTag(experience_tag_id='{self.experience_tag_id}')>"
