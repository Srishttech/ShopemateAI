"""
Lightweight JSON-file "database" layer for ShopMate AI.

Every read/write to products.json, orders.json and tickets.json goes
through this module so that the rest of the app never touches raw file
paths directly. This also makes the module easy to monkeypatch in tests.
"""

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

PRODUCTS_FILE = DATA_DIR / "products.json"
ORDERS_FILE = DATA_DIR / "orders.json"
TICKETS_FILE = DATA_DIR / "tickets.json"


def _load_json(path: Path) -> Any:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------- Products ----------

def load_products() -> list:
    return _load_json(PRODUCTS_FILE)


def save_products(products: list) -> None:
    _save_json(PRODUCTS_FILE, products)


# ---------- Orders ----------

def load_orders() -> list:
    return _load_json(ORDERS_FILE)


# ---------- Tickets ----------

def load_tickets() -> list:
    return _load_json(TICKETS_FILE)


def save_tickets(tickets: list) -> None:
    _save_json(TICKETS_FILE, tickets)
