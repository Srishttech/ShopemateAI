"""
Shared pytest fixtures.

Every test runs against an isolated, temporary copy of the JSON "database"
so tests never touch (or depend on) the real data/ files.
"""

import json
import pytest

from utils import data_manager as dm

SAMPLE_PRODUCTS = [
    {
        "id": "P101",
        "name": "Nova Sprint Running Shoes",
        "category": "Footwear",
        "brand": "Nova",
        "price": 2499,
        "description": "Lightweight running shoes with breathable mesh upper.",
        "rating": 4.3,
        "stock": 25,
    },
    {
        "id": "P102",
        "name": "Trailblaze Pro Running Shoes",
        "category": "Footwear",
        "brand": "Trailblaze",
        "price": 3499,
        "description": "Cushioned running shoes for long distance running.",
        "rating": 4.5,
        "stock": 12,
    },
    {
        "id": "P201",
        "name": "BeatPods X1 Wireless Earbuds",
        "category": "Electronics",
        "brand": "BeatPods",
        "price": 1999,
        "description": "True wireless earbuds with deep bass.",
        "rating": 4.4,
        "stock": 50,
    },
]

SAMPLE_ORDERS = [
    {
        "order_id": "ORD1001",
        "customer_name": "Aarav Sharma",
        "items": [{"product_id": "P101", "name": "Nova Sprint Running Shoes", "qty": 1, "price": 2499}],
        "status": "Shipped",
        "order_date": "2026-06-10",
        "expected_delivery": "2026-06-26",
        "total": 2499,
    }
]


@pytest.fixture(autouse=True)
def isolated_data(tmp_path, monkeypatch):
    """Point data_manager at temporary files for every test automatically."""
    products_file = tmp_path / "products.json"
    orders_file = tmp_path / "orders.json"
    tickets_file = tmp_path / "tickets.json"

    products_file.write_text(json.dumps(SAMPLE_PRODUCTS), encoding="utf-8")
    orders_file.write_text(json.dumps(SAMPLE_ORDERS), encoding="utf-8")
    tickets_file.write_text(json.dumps([]), encoding="utf-8")

    monkeypatch.setattr(dm, "PRODUCTS_FILE", products_file)
    monkeypatch.setattr(dm, "ORDERS_FILE", orders_file)
    monkeypatch.setattr(dm, "TICKETS_FILE", tickets_file)

    yield
