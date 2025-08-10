from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Defaultdocumentnotes(Base):
    __tablename__ = 'default_document_notes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_type = Column(Text, nullable=False)
    language_code = Column(Text, nullable=False)
    note_content = Column(Text, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


    def __repr__(self):
        return f'<Defaultdocumentnotes id={self.id}>'
