from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class ClientTransporters(Base):
    __tablename__ = 'client__transporters'
    client_transporter_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    transporter_id = Column(Text, ForeignKey('transporters.transporter_id'), nullable=False)

    assigned_at = Column(DateTime)


    def __repr__(self):
        return f'<ClientTransporters client_transporter_id={self.client_transporter_id}>'
    client_rel = relationship('Client')
    transporter_rel = relationship('Transporter')
