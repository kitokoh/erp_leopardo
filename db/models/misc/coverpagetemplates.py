from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Coverpagetemplates(Base):
    __tablename__ = 'cover_page_templates'
    template_id = Column(Text, primary_key=True, nullable=False, unique=True)
    default_title = Column(Text)
    style_config_json = Column(Text, nullable=False)
    created_at = Column(DateTime)
    created_by_user_id = Column(Text, ForeignKey('users.user_id'))



    def __repr__(self):
        return f'<Coverpagetemplates template_id={self.template_id}>'
    user_rel = relationship('Users')
