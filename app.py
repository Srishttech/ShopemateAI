"""
ShopMate AI - Streamlit UI

Customer  -> Streamlit UI -> LangGraph ReAct Agent -> Tool Selection -> Tools -> Response

Sidebar lets the user switch between:
  - Customer Mode (chat-based shopping help + structured order support menu)
  - Admin Mode (Excel catalog upload, catalog stats, ticket inbox)
"""

import json

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage

from agent.graph import get_compiled_graph
from agent.tools import get_order, create_ticket, get_catalog_stats
from utils import data_manager as dm
from utils.excel_processor import process_excel, ExcelValidationError
from utils.logger import get_logger

logger = get_logger("shopmate.app")

st.set_page_config(page_title="ShopMate AI", page_icon="🛍️", layout="wide")

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
defaults = {
    "mode": "Customer",
    "customer_view": "welcome",   # welcome -> chat | orders
    "order_submenu": None,        # track | cancel | return | refund
    "chat_messages": [],          # list of LangChain message objects
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🛍️ ShopMate AI")
    st.caption("AI Store Support Agent")
    mode = st.radio("Mode", ["Customer Mode", "Admin Mode"], index=0 if st.session_state.mode == "Customer" else 1)
    st.session_state.mode = "Customer" if mode == "Customer Mode" else "Admin"

    st.divider()
    if st.session_state.mode == "Customer":
        if st.button("⬅ Back to Menu", use_container_width=True):
            st.session_state.customer_view = "welcome"
            st.session_state.order_submenu = None
            st.rerun()
        if st.button("🔄 Reset Chat", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()

    st.divider()
    st.caption("Built with LangGraph + Groq (llama-3.3-70b-versatile)")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def run_agent(user_text: str) -> str:
    """Send the user's message through the LangGraph ReAct agent and
    return Meera's final text reply."""
    graph = get_compiled_graph()
    st.session_state.chat_messages.append(HumanMessage(content=user_text))

    result = graph.invoke({"messages": st.session_state.chat_messages})
    st.session_state.chat_messages = result["messages"]

    final_message = result["messages"][-1]
    return final_message.content


def render_chat_history():
    for msg in st.session_state.chat_messages:
        if isinstance(msg, HumanMessage):
            with st.chat_message("user"):
                st.markdown(msg.content)
        elif isinstance(msg, AIMessage) and msg.content:
            with st.chat_message("assistant", avatar="🛍️"):
                st.markdown(msg.content)


# ---------------------------------------------------------------------------
# CUSTOMER MODE
# ---------------------------------------------------------------------------
def customer_mode():
    if st.session_state.customer_view == "welcome":
        st.header("Hi, I'm Meera 👋")
        st.subheader("Your shopping assistant.")
        st.write("How can I help you today?")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🛒 1. Shopping Help", use_container_width=True, type="primary"):
                st.session_state.customer_view = "chat"
                st.rerun()
        with col2:
            if st.button("📦 2. My Orders", use_container_width=True):
                st.session_state.customer_view = "orders"
                st.rerun()

    elif st.session_state.customer_view == "chat":
        st.header("🛒 Shopping Help")
        st.caption(
            "Try: \"Show running shoes under ₹3000\" · \"Recommend wireless earbuds\" · "
            "\"Compare P101 and P102\" · \"Cheaper alternative to the shoes I ordered\""
        )
        render_chat_history()

        user_input = st.chat_input("Ask Meera anything about products...")
        if user_input:
            with st.chat_message("user"):
                st.markdown(user_input)
            with st.spinner("Meera is thinking..."):
                try:
                    reply = run_agent(user_input)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Agent error")
                    reply = (
                        "Sorry, I ran into a technical issue while processing that. "
                        f"({exc})"
                    )
            with st.chat_message("assistant", avatar="🛍️"):
                st.markdown(reply)

    elif st.session_state.customer_view == "orders":
        st.header("📦 My Orders")

        if st.session_state.order_submenu is None:
            st.write("What would you like to do?")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                if st.button("🔍 Track Order", use_container_width=True):
                    st.session_state.order_submenu = "track"
                    st.rerun()
            with c2:
                if st.button("❌ Cancel Order", use_container_width=True):
                    st.session_state.order_submenu = "cancel"
                    st.rerun()
            with c3:
                if st.button("↩️ Return Order", use_container_width=True):
                    st.session_state.order_submenu = "return"
                    st.rerun()
            with c4:
                if st.button("💸 Refund Issue", use_container_width=True):
                    st.session_state.order_submenu = "refund"
                    st.rerun()

        else:
            if st.button("← back"):
                st.session_state.order_submenu = None
                st.rerun()

            if st.session_state.order_submenu == "track":
                st.subheader("Track Order")
                order_id = st.text_input("Enter your Order ID (e.g. ORD1001)")
                if st.button("Track", type="primary") and order_id:
                    result = get_order.invoke({"order_id": order_id})
                    if result.startswith("NOT_FOUND"):
                        st.error(result.replace("NOT_FOUND: ", ""))
                    else:
                        order = json.loads(result)
                        product_lines = "\n".join(
                            f"- {item['name']} (Qty: {item['qty']})"
                            for item in order["items"]
                        )
                        st.markdown(f"""
📦 **Order Details**

**Order ID:** {order['order_id']}

**Product(s):**
{product_lines}

**Status:** {order['status']}

**Expected Delivery:** {order['expected_delivery']}
""")

            else:
                labels = {
                    "cancel": ("Cancel Order", "Please share your Order ID and reason for cancellation."),
                    "return": ("Return Order", "Please share your Order ID and reason for the return."),
                    "refund": ("Refund Issue", "Please describe the refund issue and your Order ID."),
                }
                title, placeholder = labels[st.session_state.order_submenu]
                st.subheader(title)
                issue_text = st.text_area("Tell us what happened", placeholder=placeholder)
                if st.button("Submit Request", type="primary") and issue_text.strip():
                    full_issue = f"[{title}] {issue_text.strip()}"
                    result = create_ticket.invoke({"issue": full_issue})
                    ticket = json.loads(result)
                    st.success(
                        f"Your request has been logged. Ticket ID: **{ticket['ticket_id']}**. "
                        "Our support team will follow up shortly."
                    )


# ---------------------------------------------------------------------------
# ADMIN MODE
# ---------------------------------------------------------------------------
def admin_mode():
    st.header("🛠️ Admin Panel")
    tab1, tab2, tab3 = st.tabs(["📤 Upload Catalog", "📊 Catalog Stats", "🎫 Tickets"])

    with tab1:
        st.subheader("Update Product Catalog")
        st.caption(
            "Upload an Excel file (.xlsx) with columns: "
            "id, name, category, brand, price, description, rating, stock"
        )
        uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx", "xls"])
        if uploaded_file is not None:
            if st.button("Replace Catalog", type="primary"):
                try:
                    summary = process_excel(uploaded_file)
                    st.success("✅ Catalog Updated Successfully")
                    st.info(f"{summary['count']} products loaded into data/products.json")
                except ExcelValidationError as exc:
                    st.error(f"Validation failed: {exc}")
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Catalog upload failed")
                    st.error(f"Unexpected error: {exc}")

    with tab2:
        st.subheader("Catalog Statistics")
        stats = json.loads(get_catalog_stats.invoke({}))
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Products", stats.get("total_products", 0))
        c2.metric("Total Brands", stats.get("total_brands", 0))
        c3.metric("Average Price", f"₹{stats.get('average_price', 0)}")
        st.write("**Products per category**")
        st.bar_chart(stats.get("categories", {}))
        with st.expander("View raw catalog"):
            st.dataframe(dm.load_products())

    with tab3:
        st.subheader("Support Tickets")
        tickets = dm.load_tickets()
        if not tickets:
            st.info("No tickets have been created yet.")
        else:
            st.dataframe(tickets, use_container_width=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if st.session_state.mode == "Customer":
    customer_mode()
else:
    admin_mode()
