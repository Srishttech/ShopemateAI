"""
Track Order feature.

Looks up an order by ID from orders.json and returns its status.
Used by the "Track Order" option in My Orders.
"""

import json

from langchain_core.tools import tool

from utils import data_manager as dm


@tool
def get_order(order_id: str) -> str:
    """
    Look up a customer order by its order ID (e.g. 'ORD1001') and return
    its status, items and delivery details as JSON. Use this for order tracking.
    Returns NOT_FOUND if the order id doesn't exist.
    """
    orders = dm.load_orders()
    clean_id = (order_id or "").strip().upper()

    for order in orders:
        if order.get("order_id", "").upper() == clean_id:
            return json.dumps(order, indent=2)

    return f"NOT_FOUND: No order found with ID '{order_id}'. Please double-check the order ID (e.g. ORD1001)."
