"""
Support Ticket feature.

Creates a ticket in tickets.json for cancellations, returns, and refund
issues. Ticket IDs follow the TKT-1001, TKT-1002... format.
"""

import json
from datetime import datetime, timezone

from langchain_core.tools import tool

from utils import data_manager as dm


@tool
def create_ticket(issue: str) -> str:
    """
    Create a support ticket for a cancellation, return, or refund request.
    Pass a clear description, including the order ID if known.
    Returns the new ticket (with ticket_id like TKT-1001) as JSON.
    """
    if not issue or not issue.strip():
        return "ERROR: An issue description is required to create a ticket."

    tickets = dm.load_tickets()

    existing_nums = [
        int(t["ticket_id"].split("-")[1])
        for t in tickets
        if t.get("ticket_id", "").startswith("TKT-") and t["ticket_id"].split("-")[1].isdigit()
    ]
    next_num = max(existing_nums) + 1 if existing_nums else 1001

    new_ticket = {
        "ticket_id": f"TKT-{next_num}",
        "issue": issue.strip(),
        "status": "Open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    tickets.append(new_ticket)
    dm.save_tickets(tickets)

    return json.dumps(new_ticket, indent=2)
