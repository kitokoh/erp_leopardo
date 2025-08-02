from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Contactlists(Base):
    __tablename__ = 'contact_lists'
    list_id = Column(Integer, primary_key=True, autoincrement=True)
    list_name = Column(Text, nullable=False, unique=True)
    description = Column(Text)
    created_by_user_id = Column(Text, ForeignKey('users.user_id'))

    created_at = Column(DateTime)
    updated_at = Column(DateTime)


    def __repr__(self):
        return f'<Contactlists list_id={self.list_id}>'
    user_rel = relationship('Users')
