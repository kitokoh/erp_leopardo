from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, REAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base
from app.models.db.products.product import Product

class ProformaInvoiceItem(Base):
    __tablename__ = 'proforma_invoice_items'

    id = Column(String, primary_key=True)
    proforma_invoice_id = Column(String, ForeignKey('proforma_invoices.id'))
    product_id = Column(Integer, ForeignKey('products.product_id'))
    description = Column(Text)
    quantity = Column(REAL)
    unit_price = Column(REAL)
    total_price = Column(REAL)

    proforma_invoice = relationship("ProformaInvoice", back_populates="items")
    product = relationship("Product", back_populates="proforma_items")

    def __repr__(self):
        return f"<ProformaInvoiceItem(id='{self.id}')>"
