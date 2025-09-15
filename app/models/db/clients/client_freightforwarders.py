from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base

class ClientFreightforwarders(Base):
    __tablename__ = 'client__freight_forwarders'
    client_forwarder_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    client_id = Column(String, ForeignKey('clients.client_id'), nullable=False)
    forwarder_id = Column(Text, ForeignKey('freight_forwarders.forwarder_id'), nullable=False)

    assigned_at = Column(DateTime)


    def __repr__(self):
        return f'<ClientFreightforwarders client_id={self.client_id} forwarder_id={self.forwarder_id}>'
    client_rel = relationship('Client')
    freightforwarder_rel = relationship('FreightForwarder')
