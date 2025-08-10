from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class ContactList(Base):
    __tablename__ = 'contact_lists'

    list_id = Column(Integer, primary_key=True, autoincrement=True)
    list_name = Column(String)
    description = Column(Text)
    created_by_user_id = Column(String, ForeignKey('users.user_id'))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<ContactList(list_id='{self.list_id}')>"
