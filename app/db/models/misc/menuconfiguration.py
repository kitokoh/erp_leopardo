from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class MenuConfiguration(Base):
    __tablename__ = 'menu_configuration'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    item_name = Column(String)
    item_order = Column(Integer)
    is_visible = Column(Boolean)
    module_identifier = Column(String)
    parent_id = Column(Integer, ForeignKey('menu_configuration.id'))

    def __repr__(self):
        return f"<MenuConfiguration(id='{self.id}')>"
