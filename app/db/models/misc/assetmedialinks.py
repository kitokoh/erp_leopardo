from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class AssetMediaLink(Base):
    __tablename__ = 'asset_media_links'

    link_id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(Text, ForeignKey('company_assets.asset_id'), nullable=False)
    media_item_id = Column(Text, ForeignKey('media_items.media_item_id'), nullable=False)
    display_order = Column(Integer, default=0)
    alt_text = Column(String)
    created_at = Column(DateTime)

    def __repr__(self):
        return f"<AssetMediaLink(link_id='{self.link_id}')>"
