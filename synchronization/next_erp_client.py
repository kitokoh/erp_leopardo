# -*- coding: utf-8 -*-

class NextERPClient:
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key

    def get_products(self):
        # Placeholder for fetching products from Next-ERP
        print("Fetching products from Next-ERP...")
        # In a real implementation, this would make an API call.
        # For now, we'll return some mock data.
        return [
            {"id": "next-erp-1", "product_name": "Produit A de Next-ERP", "price": 10.0},
            {"id": "next-erp-2", "product_name": "Produit B de Next-ERP", "price": 20.0},
        ]

    def sync_product(self, product_data):
        # Placeholder for syncing a single product to Next-ERP
        print(f"Syncing product: {product_data.get('product_name')}")
        # In a real implementation, this would make an API call.
        return {"status": "success", "id": f"next-erp-{product_data.get('id')}"}

    def delete_product(self, next_erp_id):
        # Placeholder for deleting a product from Next-ERP
        print(f"Deleting product with Next-ERP ID: {next_erp_id}")
        # In a real implementation, this would make an API call.
        return {"status": "success"}
