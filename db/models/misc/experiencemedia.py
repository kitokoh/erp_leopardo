from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class ExperienceMedia(Base):
    __tablename__ = 'experience_media'

    experience_media_id = Column(Integer, primary_key=True, autoincrement=True)
    experience_id = Column(String, ForeignKey('experiences.experience_id'))
    media_item_id = Column(String, ForeignKey('media_items.media_item_id'))
    created_at = Column(DateTime)

    def __repr__(self):
        return f"<ExperienceMedia(experience_media_id='{self.experience_media_id}')>"
