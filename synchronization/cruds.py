# -*- coding: utf-8 -*-

from db.cruds.products_crud import products_crud_instance
from db.cruds.generic_crud import _manage_conn
import logging
from typing import Dict, Any, Optional

@_manage_conn
def get_product_by_next_erp_id(next_erp_id: str, conn=None) -> Optional[Dict[str, Any]]:
    """
    Fetches a single product by its next_erp_id.
    """
    cursor = conn.cursor()
    sql = "SELECT * FROM Products WHERE next_erp_id = ?"
    try:
        cursor.execute(sql, (next_erp_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except Exception as e:
        logging.error(f"Error getting product by next_erp_id '{next_erp_id}': {e}", exc_info=True)
        return None

def add_or_update_product(product_data: dict):
    """
    Adds or updates a product based on its next_erp_id.
    """
    next_erp_id = product_data.get('id')
    if not next_erp_id:
        logging.error("Cannot add or update product without next_erp_id.")
        return

    existing_product = get_product_by_next_erp_id(next_erp_id)

    if existing_product:
        # Update existing product
        product_id = existing_product.get('product_id')
        logging.info(f"Updating existing product with local ID {product_id} from Next-ERP ID {next_erp_id}")
        products_crud_instance.update_product(product_id, product_data)
    else:
        # Create new product
        logging.info(f"Creating new product from Next-ERP ID {next_erp_id}")
        # Make sure to map the 'id' from Next-ERP to 'next_erp_id'
        product_data['next_erp_id'] = product_data.pop('id', None)
        products_crud_instance.add_product(product_data)
