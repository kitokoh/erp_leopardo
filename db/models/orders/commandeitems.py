from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Commandeitems(Base):
    __tablename__ = 'commande_items'
    item_id = Column(Text, primary_key=True)
    commande_id = Column(Text, nullable=False, ForeignKey('commandes.commande_id'))

    product_id = Column(Integer, nullable=False, ForeignKey('products.product_id'))

    description_item = Column(Text, nullable=False)
    quantity = Column(REAL, nullable=False)
    unit_price_ht = Column(REAL, nullable=False)
    vat_rate = Column(REAL)
    total_item_ht = Column(REAL, nullable=False)
    total_item_ttc = Column(REAL, nullable=False)
    weight = Column(REAL)
    dimensions_text = Column(Text)
    product_language_code = Column(Text)


    def __repr__(self):
        return f'<Commandeitems item_id={self.item_id}>'
    commande_rel = relationship('Commandes')
    product_rel = relationship('Products')
