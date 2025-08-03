from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class EntityContact(Base):
    __tablename__ = 'entity_contacts'

    entity_contact_id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(Text, nullable=False)
    entity_type = Column(Text, nullable=False)
    contact_id = Column(Integer, ForeignKey('contacts.contact_id'), nullable=False)
    role_in_entity = Column(Text)
    is_primary = Column(Boolean)
    can_receive_documents = Column(Boolean)
    notes = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<EntityContact(entity_contact_id='{self.entity_contact_id}')>"
