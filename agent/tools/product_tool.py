"""
Product Lookup feature.

Fetches a single product by ID - mainly used when the agent needs to
compare two named products (e.g. "compare P101 and P102").
"""

import json

from langchain_core.tools import tool

from utils import data_manager as dm


@tool
def get_product(product_id: str) -> str:
    """
    Get full details of a single product by its ID (e.g. 'P101').
    Useful when comparing two named products. Returns NOT_FOUND if missing.
    """
    products = dm.load_products()
    clean_id = (product_id or "").strip().upper()

    for product in products:
        if str(product.get("id", "")).upper() == clean_id:
            return json.dumps(product, indent=2)

    return f"NOT_FOUND: No product found with ID '{product_id}'."
