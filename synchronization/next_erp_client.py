# -*- coding: utf-8 -*-

class NextERPClient:
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key

    def get_products(self):
        # Placeholder for fetching products from Next-ERP
        print("Fetching products from Next-ERP...")
        return []

    def sync_product(self, product_data):
        # Placeholder for syncing a single product to Next-ERP
        print(f"Syncing product: {product_data.get('name')}")
        return {"status": "success", "id": "next-erp-123"}
