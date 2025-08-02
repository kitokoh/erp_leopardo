from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Entitycontacts(Base):
    __tablename__ = 'entity_contacts'
    entity_contact_id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(Text, nullable=False)
    entity_type = Column(Text, nullable=False)
    contact_id = Column(Integer, nullable=False, ForeignKey('contacts.contact_id'))

    role_in_entity = Column(Text)
    is_primary = Column(Boolean)
    can_receive_documents = Column(Boolean)
    notes = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


    def __repr__(self):
        return f'<Entitycontacts entity_contact_id={self.entity_contact_id}>'
    contact_rel = relationship('Contacts')
