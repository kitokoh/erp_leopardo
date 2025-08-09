from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Commandedocumentnotes(Base):
    __tablename__ = 'commande_document_notes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    commande_document_id = Column(Text, ForeignKey('client_documents.document_id'), nullable=False)
    note_content = Column(Text, nullable=False)
    language_code = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    clientdocument_rel = relationship('ClientDocument')

    def __repr__(self):
        return f'<Commandedocumentnotes id={self.id}>'
