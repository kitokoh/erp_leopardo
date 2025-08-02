from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Contacts(Base):
    __tablename__ = 'contacts'
    # = Column(String, primary_key=True, autoincrement=True)
    # = Column(String, nullable=False)
    # = Column(String, unique=True)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(Date)
    # = Column(String)
    # = Column(String)
    # = Column(Date)
    # = Column(String)
    # = Column(String, ForeignKey('users.user_id'))

    user_rel = relationship('Users')

    def __repr__(self):
        return f'<Contacts #={self.#}>'
    user_rel = relationship('Users')
