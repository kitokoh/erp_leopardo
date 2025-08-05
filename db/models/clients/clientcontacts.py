from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Clientcontacts(Base):
    __tablename__ = 'client_contacts'
    client_contact_id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Text, nullable=False, ForeignKey('clients.client_id'))

    contact_id = Column(Integer, nullable=False, ForeignKey('contacts.contact_id'))

    is_primary_for_client = Column(Boolean)
    can_receive_documents = Column(Boolean)
    added_by_user_id = Column(Text, ForeignKey('users.user_id'))

    created_at = Column(DateTime)
    updated_at = Column(DateTime)


    def __repr__(self):
        return f'<Clientcontacts client_contact_id={self.client_contact_id}>'
    client_rel = relationship('Clients')
    contact_rel = relationship('Contacts')
    user_rel = relationship('Users')
