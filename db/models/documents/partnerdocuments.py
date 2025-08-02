from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Partnerdocuments(Base):
    __tablename__ = 'partner_documents'
    document_id = Column(Text, primary_key=True, nullable=False)
    file_path_relative = Column(Text, nullable=False)
    created_at = Column(DateTime)


    def __repr__(self):
        return f'<Partnerdocuments document_id={self.document_id}>'
