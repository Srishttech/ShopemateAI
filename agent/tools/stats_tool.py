"""
Catalog Stats feature.

Quick summary stats over products.json (used in the Admin dashboard).
"""

import json

from langchain_core.tools import tool

from utils import data_manager as dm


@tool
def get_catalog_stats() -> str:
    """
    Return catalog stats: total products, products per category, distinct
    brands, average price. Used in the Admin dashboard.
    """
    products = dm.load_products()
    if not products:
        return json.dumps({"total_products": 0, "categories": {}, "total_brands": 0, "average_price": 0})

    categories = {}
    brands = set()
    total_price = 0.0

    for product in products:
        category = product.get("category", "Unknown")
        categories[category] = categories.get(category, 0) + 1
        brands.add(product.get("brand", "Unknown"))
        total_price += float(product.get("price", 0))

    stats = {
        "total_products": len(products),
        "categories": categories,
        "total_brands": len(brands),
        "average_price": round(total_price / len(products), 2),
    }
    return json.dumps(stats, indent=2)
