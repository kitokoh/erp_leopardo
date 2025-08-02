from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Coverpages(Base):
    __tablename__ = 'cover_pages'
    cover_page_id = Column(Text, primary_key=True)
    template_id = Column(Text, nullable=False, ForeignKey('coverpagetemplates.template_id'))

    institution_text = Column(Text)
    document_version = Column(Text)
    custom_style_config_json = Column(Text)
    created_at = Column(DateTime)
    created_by_user_id = Column(Text, ForeignKey('users.user_id'))



    def __repr__(self):
        return f'<Coverpages cover_page_id={self.cover_page_id}>'
    client_rel = relationship('Clients')
    project_rel = relationship('Projects')
    coverpagetemplate_rel = relationship('Coverpagetemplates')
    user_rel = relationship('Users')
