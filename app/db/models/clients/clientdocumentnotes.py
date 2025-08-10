from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Clientdocumentnotes(Base):
    __tablename__ = 'client_document_notes'
    note_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    client_id = Column(String, ForeignKey('clients.client_id'), nullable=False)
    document_type = Column(Text, nullable=False)
    note_content = Column(Text, nullable=False)
    created_at = Column(DateTime)


    def __repr__(self):
        return f'<Clientdocumentnotes note_id={self.note_id}>'
    client_rel = relationship('Client')
