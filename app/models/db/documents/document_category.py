from sqlalchemy import Column, Integer, String, Text
from app.db.connection import Base

class DocumentCategory(Base):
    __tablename__ = 'document_categories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)

    def __repr__(self):
        return f"<DocumentCategory(id={self.id}, name='{self.name}')>"
