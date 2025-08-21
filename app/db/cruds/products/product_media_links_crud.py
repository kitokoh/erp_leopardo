from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, update, delete
from app.models.db.products.productmedialinks import ProductMediaLink
from app.media_manager.models import MediaItem
import logging
from typing import List, Optional

class ProductMediaLinksCRUD:
    def link_media_to_product(self, db: Session, product_id: int, media_item_id: str, display_order: int = 0, alt_text: Optional[str] = None) -> Optional[ProductMediaLink]:
        """Links a media item to a product."""
        try:
            new_link = ProductMediaLink(
                product_id=product_id,
                media_item_id=media_item_id,
                display_order=display_order,
                alt_text=alt_text
            )
            db.add(new_link)
            db.commit()
            db.refresh(new_link)
            return new_link
        except Exception as e:
            db.rollback()
            logging.error(f"Error linking media {media_item_id} to product {product_id}: {e}")
            return None

    def get_media_links_for_product(self, db: Session, product_id: int) -> List[ProductMediaLink]:
        """Retrieves all media links for a given product, ordered by display_order."""
        return db.query(ProductMediaLink).join(MediaItem).filter(ProductMediaLink.product_id == product_id).order_by(ProductMediaLink.display_order).all()

    def get_media_link_by_ids(self, db: Session, product_id: int, media_item_id: str) -> Optional[ProductMediaLink]:
        """Retrieves a specific media link by product_id and media_item_id."""
        return db.query(ProductMediaLink).filter_by(product_id=product_id, media_item_id=media_item_id).first()

    def get_media_link_by_link_id(self, db: Session, link_id: int) -> Optional[ProductMediaLink]:
        """Retrieves a specific media link by its link_id."""
        return db.query(ProductMediaLink).filter_by(link_id=link_id).first()

    def update_media_link(self, db: Session, link_id: int, display_order: Optional[int] = None, alt_text: Optional[str] = None) -> bool:
        """Updates a media link."""
        link = self.get_media_link_by_link_id(db, link_id)
        if not link:
            return False

        if display_order is not None:
            link.display_order = display_order
        if alt_text is not None:
            link.alt_text = alt_text

        db.commit()
        return True

    def unlink_media_from_product(self, db: Session, link_id: int) -> bool:
        """Removes a media link by its link_id."""
        link = self.get_media_link_by_link_id(db, link_id)
        if link:
            db.delete(link)
            db.commit()
            return True
        return False

    def unlink_all_media_from_product(self, db: Session, product_id: int) -> int:
        """Removes all media links for a given product."""
        num_deleted = db.query(ProductMediaLink).filter_by(product_id=product_id).delete()
        db.commit()
        return num_deleted

    def update_product_media_display_orders(self, db: Session, product_id: int, ordered_media_item_ids: List[str]) -> bool:
        """Updates the display_order for all media items linked to a product."""
        try:
            with db.begin_nested():
                for index, media_item_id in enumerate(ordered_media_item_ids):
                    db.query(ProductMediaLink).filter_by(
                        product_id=product_id,
                        media_item_id=media_item_id
                    ).update({'display_order': index})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logging.error(f"Error updating display orders for product {product_id}: {e}")
            return False

product_media_links_crud = ProductMediaLinksCRUD()
