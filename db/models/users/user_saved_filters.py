from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class UserSavedFilters(Base):
    __tablename__ = 'user_saved_filters'
    id = Column(Text, primary_key=True)
    user_id = Column(Text, nullable=False, ForeignKey('users.user_id'))

    filter_name = Column(Text, nullable=False)
    filter_parameters_json = Column(Text, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


    def __repr__(self):
        return f'<UserSavedFilters id={self.id}>'
    user_rel = relationship('Users')
