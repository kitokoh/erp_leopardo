from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Invoices(Base):
    __tablename__ = 'invoices'
    invoice_id = Column(Text, primary_key=True)
    client_id = Column(Text, nullable=False, ForeignKey('clients.client_id'))

    project_id = Column(Text, ForeignKey('projects.project_id'))

    document_id = Column(Text, ForeignKey('clientdocuments.document_id'))

    invoice_number = Column(Text, nullable=False, unique=True)
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    total_amount = Column(REAL, nullable=False)
    currency = Column(Text, nullable=False)
    payment_status = Column(Text, nullable=False)
    payment_date = Column(Date)
    payment_method = Column(Text)
    transaction_id = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


    def __repr__(self):
        return f'<Invoices invoice_id={self.invoice_id}>'
    client_rel = relationship('Clients')
    project_rel = relationship('Projects')
    clientdocument_rel = relationship('Clientdocuments')
