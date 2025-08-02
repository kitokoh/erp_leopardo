from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class CompanyFactures(Base):
    __tablename__ = 'company_factures'
    facture_id = Column(Integer, primary_key=True, autoincrement=True)
    original_file_name = Column(Text, nullable=False)
    stored_file_path = Column(Text, nullable=False)
    file_mime_type = Column(Text)
    upload_date = Column(DateTime)
    extraction_status = Column(Text, nullable=False)
    extracted_data_json = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    is_deleted = Column(Integer)
    deleted_at = Column(DateTime)


    def __repr__(self):
        return f'<CompanyFactures facture_id={self.facture_id}>'
