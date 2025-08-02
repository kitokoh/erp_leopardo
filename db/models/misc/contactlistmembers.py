from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Contactlistmembers(Base):
    __tablename__ = 'contact_list_members'
    list_member_id = Column(Integer, primary_key=True, autoincrement=True)
    list_id = Column(Integer, nullable=False, ForeignKey('contactlists.list_id'))

    contact_id = Column(Integer, nullable=False, ForeignKey('contacts.contact_id'))

    added_at = Column(DateTime)


    def __repr__(self):
        return f'<Contactlistmembers list_member_id={self.list_member_id}>'
    contactlist_rel = relationship('Contactlists')
    contact_rel = relationship('Contacts')
