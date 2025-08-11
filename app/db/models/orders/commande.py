from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, REAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class Commande(Base):
    __tablename__ = 'commandes'

    commande_id = Column(String, primary_key=True)
    client_id = Column(String, ForeignKey('clients.client_id'))
    project_id = Column(String, ForeignKey('projects.project_id'))
    commande_reference = Column(String, unique=True, nullable=False)
    commande_date = Column(DateTime, server_default=func.now(), nullable=False)
    status_commande_id = Column(Integer, ForeignKey('status_settings.status_id'))
    description_commande = Column(Text)
    notes = Column(Text)
    is_default = Column(Boolean, default=False)
    total_ht = Column(REAL)
    total_ttc = Column(REAL)
    currency = Column(String, nullable=False, default='EUR')
    shipping_address = Column(Text)
    billing_address = Column(Text)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by_user_id = Column(String, ForeignKey('users.user_id'))
    deleted_at = Column(DateTime)

    client = relationship("Client")
    project = relationship("Project")
    status = relationship("StatusSetting")
    creator = relationship("User")
    __table_args__ = {'extend_existing': True}

    def __repr__(self):
        return f"<Commande(commande_id='{self.commande_id}', commande_reference='{self.commande_reference}')>"
