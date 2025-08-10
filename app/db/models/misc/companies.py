from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Company(Base):
    __tablename__ = 'companies'

    company_id = Column(String, primary_key=True)
    company_name = Column(String)
    address = Column(Text)
    payment_info = Column(Text)
    logo_path = Column(String)
    other_info = Column(Text)
    is_default = Column(Boolean)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    proforma_invoices = relationship("ProformaInvoice", back_populates="company")

    def __repr__(self):
        return f"<Company(company_id='{self.company_id}')>"
