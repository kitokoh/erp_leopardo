from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Invoice(Base):
    __tablename__ = 'invoices'

    invoice_id = Column(String, primary_key=True)
    client_id = Column(Text, ForeignKey('clients.client_id'), nullable=False)
    project_id = Column(Text, ForeignKey('projects.project_id'))
    document_id = Column(Text, ForeignKey('client_documents.document_id'))
    invoice_number = Column(String)
    issue_date = Column(Date)
    due_date = Column(Date)
    total_amount = Column(REAL)
    currency = Column(String)
    payment_status = Column(String)
    payment_date = Column(Date)
    payment_method = Column(String)
    transaction_id = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<Invoice(invoice_id='{self.invoice_id}')>"
