from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Assetmedialinks(Base):
    __tablename__ = 'asset_media_links'
    link_id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(Text, nullable=False, ForeignKey('companyassets.asset_id'))

    media_item_id = Column(Text, nullable=False, ForeignKey('mediaitems.media_item_id'))

    display_order = Column(Integer)
    alt_text = Column(Text)
    created_at = Column(DateTime)


    def __repr__(self):
        return f'<Assetmedialinks link_id={self.link_id}>'
    companyasset_rel = relationship('Companyassets')
    mediaitem_rel = relationship('Mediaitems')
