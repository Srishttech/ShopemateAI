"""
Product Search feature.

Keyword + budget based search over products.json. Used for product
search, recommendations, and "cheaper alternative" type queries.
"""

import json
import re

from langchain_core.tools import tool

from utils import data_manager as dm

_STOPWORDS = {
    "under", "below", "less", "than", "rs", "rs.", "inr", "the", "a", "an",
    "for", "of", "to", "show", "me", "find", "search", "please", "and",
}


@tool
def search_products(query: str) -> str:
    """
    Search the catalog by name/category/brand keywords, optionally with a
    budget like 'running shoes under 3000'. Returns up to 10 matches as JSON.
    Returns EMPTY_QUERY if the query is blank, NO_RESULTS if nothing matches.
    """
    if not query or not query.strip():
        return "EMPTY_QUERY: Please provide a search term, category, or budget."

    products = dm.load_products()
    q = query.lower().strip()

    max_price = None
    price_match = re.search(r"under\s*(?:rs\.?|inr|₹)?\s*(\d+)", q)
    if price_match:
        max_price = float(price_match.group(1))

    keywords = [w for w in re.findall(r"[a-zA-Z]+", q) if w not in _STOPWORDS]

    results = []
    for product in products:
        haystack = " ".join(
            str(product.get(f, "")) for f in ("name", "category", "brand", "description")
        ).lower()

        keyword_hit = any(kw in haystack for kw in keywords) if keywords else True
        price_ok = product.get("price", 0) <= max_price if max_price is not None else True

        if keyword_hit and price_ok:
            results.append(product)

    if not results:
        return f"NO_RESULTS: No products matched '{query}'. Try a different keyword or budget."

    results.sort(key=lambda p: p.get("price", 0))
    return json.dumps(results[:10], indent=2)
