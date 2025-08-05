from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class ClientFreightforwarders(Base):
    __tablename__ = 'client__freight_forwarders'
    client_forwarder_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    forwarder_id = Column(Text, nullable=False, ForeignKey('freightforwarders.forwarder_id'))

    assigned_at = Column(DateTime)


    def __repr__(self):
        return f'<ClientFreightforwarders client_forwarder_id={self.client_forwarder_id}>'
    client_rel = relationship('Clients')
    freightforwarder_rel = relationship('Freightforwarders')
