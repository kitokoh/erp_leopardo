from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Templates(Base):
    __tablename__ = 'templates'
    template_id = Column(Integer, primary_key=True, autoincrement=True)
    template_name = Column(Text, nullable=False)
    template_type = Column(Text, nullable=False)
    description = Column(Text)
    base_file_name = Column(Text)
    language_code = Column(Text)
    is_default_for_type_lang = Column(Boolean)
    category_id = Column(Integer, ForeignKey('templatecategories.category_id'))

    content_definition = Column(Text)
    email_subject_template = Column(Text)
    email_variables_info = Column(Text)
    cover_page_config_json = Column(Text)
    document_mapping_config_json = Column(Text)
    raw_template_file_data = Column(LargeBinary)
    version = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    created_by_user_id = Column(Text, ForeignKey('users.user_id'))

    client_id = Column(Text, ForeignKey('clients.client_id'))



    def __repr__(self):
        return f'<Templates template_id={self.template_id}>'
    user_rel = relationship('Users')
    templatecategorie_rel = relationship('Templatecategories')
    client_rel = relationship('Clients')
