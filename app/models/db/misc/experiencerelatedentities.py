from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base

class ExperienceRelatedEntity(Base):
    __tablename__ = 'experience_related_entities'

    experience_related_entity_id = Column(Integer, primary_key=True, autoincrement=True)
    experience_id = Column(String, ForeignKey('experiences.experience_id'))
    entity_type = Column(String)
    entity_id = Column(String)
    created_at = Column(DateTime)

    def __repr__(self):
        return f"<ExperienceRelatedEntity(experience_related_entity_id='{self.experience_related_entity_id}')>"
