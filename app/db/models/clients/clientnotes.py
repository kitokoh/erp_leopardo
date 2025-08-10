from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from db.connection import Base

class Clientnotes(Base):
    __tablename__ = 'client_notes'

    note_id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Text, ForeignKey('clients.client_id'), nullable=False)
    user_id = Column(Text, ForeignKey('users.user_id'))
    timestamp = Column(DateTime)
    note_text = Column(Text, nullable=False)

    client_rel = relationship('Client')
    user_rel = relationship('User')

    def __repr__(self):
        return f'<Clientnotes note_id={self.note_id}>'
