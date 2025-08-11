from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class ContactListMember(Base):
    __tablename__ = 'contact_list_members'

    list_member_id = Column(Integer, primary_key=True, autoincrement=True)
    list_id = Column(Integer, ForeignKey('contact_lists.list_id'), nullable=False)
    contact_id = Column(Integer, ForeignKey('contacts.contact_id'), nullable=False)
    added_at = Column(DateTime)

    def __repr__(self):
        return f"<ContactListMember(list_member_id='{self.list_member_id}')>"
