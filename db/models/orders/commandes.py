from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Commandes(Base):
    __tablename__ = 'commandes'
    commande_id = Column(Text, primary_key=True)
    client_id = Column(Text, nullable=False, ForeignKey('clients.client_id'))

    project_id = Column(Text, ForeignKey('projects.project_id'))

    commande_reference = Column(Text, nullable=False, unique=True)
    commande_date = Column(DateTime, nullable=False)
    status_commande_id = Column(Integer, nullable=False, ForeignKey('statussettings.status_id'))

    description_commande = Column(Text)
    notes = Column(Text)
    is_default = Column(Boolean)
    total_ht = Column(REAL)
    total_ttc = Column(REAL)
    currency = Column(Text, nullable=False)
    shipping_address = Column(Text)
    billing_address = Column(Text)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    created_by_user_id = Column(Text, ForeignKey('users.user_id'))

    deleted_at = Column(Text)


    def __repr__(self):
        return f'<Commandes commande_id={self.commande_id}>'
    client_rel = relationship('Clients')
    project_rel = relationship('Projects')
    statussetting_rel = relationship('Statussettings')
    user_rel = relationship('Users')
