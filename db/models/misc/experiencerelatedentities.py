from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Experiencerelatedentities(Base):
    __tablename__ = 'experience_related_entities'
    experience_related_entity_id = Column(Integer, primary_key=True, autoincrement=True)
    experience_id = Column(Text, nullable=False)
    entity_type = Column(Text, nullable=False)
    entity_id = Column(Text, nullable=False)
    created_at = Column(DateTime)


    def __repr__(self):
        return f'<Experiencerelatedentities experience_related_entity_id={self.experience_related_entity_id}>'
