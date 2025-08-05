from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class ProductMediaLink(Base):
    __tablename__ = 'product_media_links'

    link_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.product_id'), nullable=False)
    media_item_id = Column(String, ForeignKey('media_items.media_item_id'), nullable=False)
    display_order = Column(Integer, default=0)
    alt_text = Column(String)
    created_at = Column(DateTime)

    def __repr__(self):
        return f"<ProductMediaLink(link_id='{self.link_id}')>"
