from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Contact(Base):
    __tablename__ = 'contacts'

    contact_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    position = Column(String)
    company_name = Column(String)
    notes = Column(Text)
    givenName = Column(String)
    familyName = Column(String)
    displayName = Column(String)
    phone_type = Column(String)
    email_type = Column(String)
    address_formattedValue = Column(String)
    address_streetAddress = Column(String)
    address_city = Column(String)
    address_region = Column(String)
    address_postalCode = Column(String)
    address_country = Column(String)
    organization_name = Column(String)
    organization_title = Column(String)
    birthday_date = Column(String)
    created_by_user_id = Column(String, ForeignKey('users.user_id'))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    employee_status = Column(String)

    creator = relationship("User")

    def __repr__(self):
        return f"<Contact(contact_id='{self.contact_id}')>"
