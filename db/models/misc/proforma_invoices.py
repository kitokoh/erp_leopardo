import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base
from ..clients.client import Client
from ..projects.project import Project
from ..misc.companies import Company
from ..documents.client_documents import ClientDocument

class ProformaInvoiceStatusEnum(enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    INVOICED = "invoiced"
    CANCELLED = "cancelled"

class ProformaInvoice(Base):
    __tablename__ = 'proforma_invoices'

    id = Column(String, primary_key=True)
    proforma_invoice_number = Column(String, unique=True, nullable=False)
    client_id = Column(String, ForeignKey('clients.client_id'), nullable=False)
    project_id = Column(String, ForeignKey('projects.project_id'))
    company_id = Column(String, ForeignKey('companies.company_id'), nullable=False)
    created_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    sent_date = Column(DateTime(timezone=True))
    status = Column(SQLAlchemyEnum(ProformaInvoiceStatusEnum), nullable=False, default=ProformaInvoiceStatusEnum.DRAFT)
    currency = Column(String(3), nullable=False, default="USD")
    subtotal_amount = Column(Float, nullable=False, default=0.0)
    discount_amount = Column(Float, nullable=True, default=0.0)
    vat_amount = Column(Float, nullable=False, default=0.0)
    grand_total_amount = Column(Float, nullable=False, default=0.0)
    payment_terms = Column(String)
    delivery_terms = Column(String)
    incoterms = Column(String)
    named_place_of_delivery = Column(String)
    notes = Column(Text)
    linked_document_id = Column(String, ForeignKey('client_documents.document_id'))
    generated_invoice_id = Column(String, ForeignKey('client_documents.document_id'))

    client = relationship("Client")
    project = relationship("Project")
    company = relationship("Company", back_populates="proforma_invoices")
    linked_document = relationship("ClientDocument", foreign_keys=[linked_document_id])
    generated_invoice_document = relationship("ClientDocument", foreign_keys=[generated_invoice_id])
    items = relationship("ProformaInvoiceItem", back_populates="proforma_invoice")

    def __repr__(self):
        return f"<ProformaInvoice(id='{self.id}')>"
