from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class CoverPageTemplate(Base):
    __tablename__ = 'cover_page_templates'

    template_id = Column(String, primary_key=True)
    template_name = Column(String)
    description = Column(Text)
    default_title = Column(String)
    default_subtitle = Column(String)
    default_author = Column(String)
    style_config_json = Column(Text)
    is_default_template = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    created_by_user_id = Column(String, ForeignKey('users.user_id'))

    def __repr__(self):
        return f"<CoverPageTemplate(template_id='{self.template_id}')>"
