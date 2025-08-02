from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Savtickets(Base):
    __tablename__ = 'sav_tickets'
    ticket_id = Column(Text, primary_key=True, nullable=False)
    client_project_product_id = Column(Integer, nullable=False, ForeignKey('clientprojectproducts.client_project_product_id'))

    status_id = Column(Integer, nullable=False, ForeignKey('statussettings.status_id'))

    resolution_details = Column(Text)
    closed_at = Column(DateTime)


    def __repr__(self):
        return f'<Savtickets ticket_id={self.ticket_id}>'
    client_rel = relationship('Clients')
    clientprojectproduct_rel = relationship('Clientprojectproducts')
    statussetting_rel = relationship('Statussettings')
    teammember_rel = relationship('Teammembers')
    user_rel = relationship('Users')
