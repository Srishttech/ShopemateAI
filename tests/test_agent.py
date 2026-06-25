"""
Unit tests for ShopMate AI tools.

Covers:
- Valid order lookup
- Invalid order lookup
- Product search (match found)
- Empty search query
- Ticket generation (including sequential numbering)
"""

import json

from agent.tools import (
    get_order,
    search_products,
    get_product,
    create_ticket,
    get_catalog_stats,
)


# ---------------------------------------------------------------------------
# get_order
# ---------------------------------------------------------------------------

def test_valid_order_returns_details():
    result = get_order.invoke({"order_id": "ORD1001"})
    data = json.loads(result)
    assert data["order_id"] == "ORD1001"
    assert data["customer_name"] == "Aarav Sharma"
    assert data["status"] == "Shipped"


def test_invalid_order_returns_not_found():
    result = get_order.invoke({"order_id": "ORD9999"})
    assert result.startswith("NOT_FOUND")


def test_order_lookup_is_case_insensitive():
    result = get_order.invoke({"order_id": "ord1001"})
    data = json.loads(result)
    assert data["order_id"] == "ORD1001"


# ---------------------------------------------------------------------------
# search_products
# ---------------------------------------------------------------------------

def test_product_search_finds_match():
    result = search_products.invoke({"query": "running shoes"})
    assert "NO_RESULTS" not in result
    data = json.loads(result)
    assert len(data) >= 1
    assert all("Running" in p["name"] for p in data)


def test_product_search_with_budget_filter():
    result = search_products.invoke({"query": "running shoes under 3000"})
    data = json.loads(result)
    assert all(p["price"] <= 3000 for p in data)
    names = [p["name"] for p in data]
    assert "Nova Sprint Running Shoes" in names
    assert "Trailblaze Pro Running Shoes" not in names  # price 3499 > 3000


def test_empty_search_query_is_handled_gracefully():
    result = search_products.invoke({"query": ""})
    assert result.startswith("EMPTY_QUERY")


def test_search_with_no_matches_returns_no_results():
    result = search_products.invoke({"query": "spaceship rocket fuel"})
    assert result.startswith("NO_RESULTS")


# ---------------------------------------------------------------------------
# get_product
# ---------------------------------------------------------------------------

def test_get_product_valid():
    result = get_product.invoke({"product_id": "P101"})
    data = json.loads(result)
    assert data["name"] == "Nova Sprint Running Shoes"


def test_get_product_invalid():
    result = get_product.invoke({"product_id": "P999"})
    assert result.startswith("NOT_FOUND")


# ---------------------------------------------------------------------------
# create_ticket
# ---------------------------------------------------------------------------

def test_ticket_generation_creates_expected_id():
    result = create_ticket.invoke({"issue": "Cancel order ORD1001"})
    ticket = json.loads(result)
    assert ticket["ticket_id"] == "TKT-1001"
    assert ticket["status"] == "Open"
    assert ticket["issue"] == "Cancel order ORD1001"


def test_ticket_ids_increment_sequentially():
    first = json.loads(create_ticket.invoke({"issue": "Return order ORD1001"}))
    second = json.loads(create_ticket.invoke({"issue": "Refund issue for ORD1001"}))
    assert first["ticket_id"] == "TKT-1001"
    assert second["ticket_id"] == "TKT-1002"


def test_ticket_requires_issue_description():
    result = create_ticket.invoke({"issue": ""})
    assert result.startswith("ERROR")


# ---------------------------------------------------------------------------
# get_catalog_stats
# ---------------------------------------------------------------------------

def test_catalog_stats_basic():
    result = get_catalog_stats.invoke({})
    stats = json.loads(result)
    assert stats["total_products"] == 3
    assert "Footwear" in stats["categories"]
