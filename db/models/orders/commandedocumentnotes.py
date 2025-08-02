from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Commandedocumentnotes(Base):
    __tablename__ = 'commande_document_notes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    commande_document_id = Column(Text, nullable=False, ForeignKey('clientdocuments.document_id'))

    note_content = Column(Text, nullable=False)
    language_code = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    -- = Column(String, ForeignKey('clientdocuments.document_id'))
    -- = Column(String)
    -- = Column(String)

    clientdocument_rel = relationship('Clientdocuments')

    def __repr__(self):
        return f'<Commandedocumentnotes id={self.id}>'
    clientdocument_rel = relationship('Clientdocuments')
