from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Projects(Base):
    __tablename__ = 'projects'
    # = Column(String, primary_key=True)
    # = Column(String, nullable=False)
    # = Column(String, nullable=False)
    # = Column(String)
    # = Column(Date)
    # = Column(Date)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(Date)
    # = Column(String, ForeignKey('clients.client_id'))
    # = Column(String, ForeignKey('statussettings.status_id'))
    # = Column(String, ForeignKey('users.user_id'))

    client_rel = relationship('Clients')
    statussetting_rel = relationship('Statussettings')
    user_rel = relationship('Users')

    def __repr__(self):
        return f'<Projects #={self.#}>'
    client_rel = relationship('Clients')
    statussetting_rel = relationship('Statussettings')
    user_rel = relationship('Users')
