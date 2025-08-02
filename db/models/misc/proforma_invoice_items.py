from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class ProformaInvoiceItems(Base):
    __tablename__ = 'proforma_invoice_items'
    # = Column(String, primary_key=True)
    # = Column(String, nullable=False)
    # = Column(String)
    # = Column(String, nullable=False)
    # = Column(String, nullable=False)
    # = Column(String, nullable=False)
    # = Column(String, nullable=False)
    # = Column(String, ForeignKey('proforma_invoices.id'))
    # = Column(String, ForeignKey('products.product_id'))

    proforma_invoice_rel = relationship('ProformaInvoices')
    product_rel = relationship('Products')

    def __repr__(self):
        return f'<ProformaInvoiceItems #={self.#}>'
    proforma_invoice_rel = relationship('ProformaInvoices')
    product_rel = relationship('Products')
