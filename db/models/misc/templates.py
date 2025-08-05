from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Template(Base):
    __tablename__ = 'templates'

    template_id = Column(Integer, primary_key=True, autoincrement=True)
    template_name = Column(String)
    template_type = Column(String)
    description = Column(Text)
    base_file_name = Column(String)
    language_code = Column(String)
    is_default_for_type_lang = Column(Boolean)
    category_id = Column(Integer, ForeignKey('template_categories.category_id'))
    content_definition = Column(Text)
    email_subject_template = Column(Text)
    email_variables_info = Column(Text)
    cover_page_config_json = Column(Text)
    document_mapping_config_json = Column(Text)
    raw_template_file_data = Column(LargeBinary)
    version = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    created_by_user_id = Column(String, ForeignKey('users.user_id'))
    client_id = Column(String, ForeignKey('clients.client_id'))

    def __repr__(self):
        return f"<Template(template_id='{self.template_id}')>"
