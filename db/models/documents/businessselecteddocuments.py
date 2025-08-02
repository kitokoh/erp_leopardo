from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Businessselecteddocuments(Base):
    __tablename__ = 'business_selected_documents'
    id = Column(Integer, primary_key=True, autoincrement=True)
    business_profile_id = Column(Integer, nullable=False)
    document_type_id = Column(Integer, nullable=False)


    def __repr__(self):
        return f'<Businessselecteddocuments id={self.id}>'
