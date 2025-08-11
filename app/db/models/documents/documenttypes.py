from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class Documenttypes(Base):
    __tablename__ = 'document_types'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True)
    description = Column(Text)


    def __repr__(self):
        return f'<Documenttypes id={self.id}>'
