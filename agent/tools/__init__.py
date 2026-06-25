"""
Tools package for ShopMate AI.

Each tool is its own file under agent/tools/ so a single feature can be
found and edited without touching the others:

    order_tool.py   -> Track Order
    search_tool.py  -> Product Search / Recommendations
    product_tool.py -> Product Lookup (used for comparisons)
    ticket_tool.py  -> Cancel / Return / Refund tickets
    stats_tool.py   -> Admin catalog stats

Everything is re-exported here so the rest of the app can still do
`from agent.tools import get_order, search_products, ...`
"""

from agent.tools.order_tool import get_order
from agent.tools.search_tool import search_products
from agent.tools.product_tool import get_product
from agent.tools.ticket_tool import create_ticket
from agent.tools.stats_tool import get_catalog_stats

ALL_TOOLS = [get_order, search_products, get_product, create_ticket, get_catalog_stats]
