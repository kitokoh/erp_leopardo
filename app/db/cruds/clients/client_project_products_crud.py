from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from uuid import uuid4
from datetime import datetime

from app.models.db.clients.clientprojectproducts import ClientProjectProduct
from app.models.db.products.product import Product
from app.db.cruds.products.products_crud import products_crud


class ClientProjectProductsCRUD:
    def add_product_to_client_or_project(self, db: Session, link_data: Dict[str, Any]) -> Optional[ClientProjectProduct]:
        product_id = link_data.get('product_id')
        client_id = link_data.get('client_id')

        if not product_id or not client_id:
            return None

        prod_info = products_crud.get_product_by_id(db, product_id)
        if not prod_info:
            return None

        qty = link_data.get('quantity', 1)
        override_price = link_data.get('unit_price_override')
        eff_price = override_price if override_price is not None else prod_info.base_unit_price

        if eff_price is None:
            eff_price = 0.0

        total_price = qty * float(eff_price)

        new_link = ClientProjectProduct(
            client_id=client_id,
            project_id=link_data.get('project_id'),
            product_id=product_id,
            quantity=qty,
            unit_price_override=override_price,
            total_price_calculated=total_price,
            serial_number=link_data.get('serial_number'),
            purchase_confirmed_at=link_data.get('purchase_confirmed_at'),
            added_by_user_id=link_data.get('added_by_user_id'),
            client_specific_product_name=link_data.get('client_specific_product_name'),
            line_description=link_data.get('line_description'),
            line_weight=link_data.get('line_weight'),
            line_dimensions_notes=link_data.get('line_dimensions_notes'),
        )
        db.add(new_link)
        db.commit()
        db.refresh(new_link)
        return new_link

    def get_products_for_client_or_project(self, db: Session, client_id: str, project_id: Optional[str] = None) -> List[ClientProjectProduct]:
        query = db.query(ClientProjectProduct).filter(ClientProjectProduct.client_id == client_id)
        if project_id is not None:
            if project_id == '__NONE__':
                query = query.filter(ClientProjectProduct.project_id.is_(None))
            else:
                query = query.filter(ClientProjectProduct.project_id == project_id)
        return query.all()

    def get_client_project_product_by_id(self, db: Session, link_id: int) -> Optional[ClientProjectProduct]:
        return db.query(ClientProjectProduct).filter(ClientProjectProduct.client_project_product_id == link_id).first()

    def remove_product_from_client_or_project(self, db: Session, link_id: int) -> bool:
        db_link = self.get_client_project_product_by_id(db, link_id)
        if db_link:
            db.delete(db_link)
            db.commit()
            return True
        return False

    def update_client_project_product(self, db: Session, link_id: int, data: Dict[str, Any]) -> Optional[ClientProjectProduct]:
        db_link = self.get_client_project_product_by_id(db, link_id)
        if not db_link:
            return None

        # Recalculate total price if needed
        qty = data.get('quantity', db_link.quantity)
        override_price = data.get('unit_price_override', db_link.unit_price_override)
        base_price = db_link.product.base_unit_price
        eff_price = override_price if override_price is not None else base_price
        if eff_price is None:
            eff_price = 0.0

        if 'quantity' in data or 'unit_price_override' in data:
            data['total_price_calculated'] = qty * float(eff_price)

        for key, value in data.items():
            setattr(db_link, key, value)

        db.commit()
        db.refresh(db_link)
        return db_link


client_project_products_crud = ClientProjectProductsCRUD()
