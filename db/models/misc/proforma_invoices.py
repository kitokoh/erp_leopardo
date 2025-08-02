from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class ProformaInvoices(Base):
    __tablename__ = 'proforma_invoices'
    # = Column(String, primary_key=True)
    # = Column(String, nullable=False, unique=True)
    # = Column(String, nullable=False)
    # = Column(String)
    # = Column(String, nullable=False)
    # = Column(Date, nullable=False)
    # = Column(Date)
    # = Column(String, nullable=False)
    # = Column(String, nullable=False)
    # = Column(String, nullable=False)
    # = Column(String)
    # = Column(String, nullable=False)
    # = Column(String, nullable=False)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String, ForeignKey('clients.client_id'))
    # = Column(String, ForeignKey('projects.project_id'))
    # = Column(String, ForeignKey('companies.company_id'))
    # = Column(String, ForeignKey('clientdocuments.document_id'))
    # = Column(String, ForeignKey('clientdocuments.document_id'))

    client_rel = relationship('Clients')
    project_rel = relationship('Projects')
    companie_rel = relationship('Companies')
    clientdocument_rel = relationship('Clientdocuments')
    clientdocument_rel = relationship('Clientdocuments')

    def __repr__(self):
        return f'<ProformaInvoices #={self.#}>'
    client_rel = relationship('Clients')
    project_rel = relationship('Projects')
    companie_rel = relationship('Companies')
    clientdocument_rel = relationship('Clientdocuments')
    clientdocument_rel = relationship('Clientdocuments')
