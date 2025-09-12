from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base

class CoverPage(Base):
    __tablename__ = 'cover_pages'

    cover_page_id = Column(String, primary_key=True)
    cover_page_name = Column(String)
    client_id = Column(String, ForeignKey('clients.client_id'))
    project_id = Column(String, ForeignKey('projects.project_id'))
    template_id = Column(Text, ForeignKey('cover_page_templates.template_id'), nullable=False)
    title = Column(String)
    subtitle = Column(String)
    author_text = Column(String)
    institution_text = Column(String)
    department_text = Column(String)
    document_type_text = Column(String)
    document_version = Column(String)
    creation_date = Column(Date)
    logo_name = Column(String)
    logo_data = Column(LargeBinary)
    custom_style_config_json = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    created_by_user_id = Column(String, ForeignKey('users.user_id'))

    def __repr__(self):
        return f"<CoverPage(cover_page_id='{self.cover_page_id}')>"
