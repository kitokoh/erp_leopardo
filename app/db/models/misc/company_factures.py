from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, false
from db.connection import Base

class CompanyFacture(Base):
    __tablename__ = 'company_factures'

    facture_id = Column(Integer, primary_key=True, autoincrement=True)
    original_file_name = Column(String)
    stored_file_path = Column(String)
    file_mime_type = Column(String)
    upload_date = Column(DateTime)
    extraction_status = Column(String)
    extracted_data_json = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    is_deleted = Column(Boolean, nullable=False, server_default=false())
    deleted_at = Column(DateTime)

    def __repr__(self):
        return f"<CompanyFacture(facture_id='{self.facture_id}')>"
