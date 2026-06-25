# 🛍️ ShopMate AI

A production-style **AI Store Support Agent** built with **Python, LangGraph, LangChain, Groq (ChatGroq), and Streamlit**.

ShopMate AI plays the role of **Meera**, a friendly shopping assistant who can search products, give recommendations, compare items, suggest cheaper alternatives, track orders, and raise support tickets for cancellations, returns, and refunds — all backed by a transparent **LangGraph ReAct workflow** that never fabricates products or orders.

---

## 📖 Project Overview

| | |
|---|---|
| **Project Name** | ShopMate AI |
| **LLM Provider** | Groq (`ChatGroq`) — **no OpenAI used anywhere** |
| **Model** | `llama-3.3-70b-versatile` |
| **Orchestration** | LangGraph (custom ReAct-style graph) |
| **Frontend** | Streamlit (Customer Mode + Admin Mode) |
| **Database** | JSON files (`products.json`, `orders.json`, `tickets.json`) |
| **Excel Processing** | Pandas (Admin catalog upload) |
| **Tests** | Pytest (13 unit tests) |

### Key capabilities

**Customer Mode**
- 🛒 **Shopping Help** — conversational chat for product search, recommendations, comparisons, and cheaper alternatives.
- 📦 **My Orders** — structured menu for Track Order / Cancel Order / Return Order / Refund Issue, generating a real support ticket (`TKT-1001`, `TKT-1002`, …) when needed.

**Admin Mode**
- 📤 Upload an Excel catalog → validated with Pandas → converted to JSON → replaces `products.json`.
- 📊 Live catalog statistics (total products, categories, brands, average price).
- 🎫 View all support tickets raised by customers.

The agent is explicitly instructed to **never invent data** — every product, order, or ticket fact in its replies comes from a tool call against the JSON files, and it gracefully reports "not found" / "no results" instead of guessing.

---

## 🏗️ Architecture Diagram

```
                ┌────────────┐
                │  Customer  │
                └─────┬──────┘
                      │
                      v
              ┌───────────────┐
              │ Streamlit UI  │  (Customer Mode / Admin Mode)
              └───────┬───────┘
                      │  user message
                      v
        ┌─────────────────────────────┐
        │   LangGraph ReAct Workflow  │
        │                             │
        │      START                  │
        │        │                    │
        │        v                    │
        │   ┌──────────┐   tool_calls?│
        │   │  agent   │──────yes─────┤
        │   │ (ChatGroq)│             │
        │   └────┬─────┘              │
        │        │ no                 v
        │        │            ┌──────────────┐
        │        │            │    tools     │
        │        │            │ (tool exec)  │
        │        │            └──────┬───────┘
        │        │                   │
        │        │   <───loop back───┘
        │        v
        │       END
        └─────────────┬───────────────┘
                       │ final answer
                       v
              ┌────────────────┐
              │ Customer-facing│
              │    response    │
              └────────────────┘

Tools available to the agent:
  get_order(order_id)        -> orders.json
  search_products(query)     -> products.json
  get_product(product_id)    -> products.json
  create_ticket(issue)       -> tickets.json
  get_catalog_stats()        -> products.json
```

The agent **chains tools automatically** when needed — e.g. for *"cheaper alternative to the shoes I ordered"*, it first calls `get_order` to discover what was purchased, then calls `search_products` with the relevant category/price to find a cheaper match.

---
## RUNNING INSTRUCTION IN CLOUD
```
 git clone https://github.com/Srishttech/ShopemateAI.git
nano .env # store your API KEY here in the formal GROQ_API_KEY= YOUR_API
chmod +x run.sh
./run.sh

## 📂 Folder Structure

```
shopmate-ai/
├── app.py                     # Streamlit UI (Customer Mode + Admin Mode)
├── agent/
│   ├── __init__.py
│   ├── llm.py                 # ChatGroq factory (GROQ_API_KEY, llama-3.3-70b-versatile)
│   ├── tools.py                # LangChain tools (get_order, search_products, ...)
│   └── graph.py                # LangGraph ReAct workflow (StateGraph)
├── utils/
│   ├── __init__.py
│   ├── data_manager.py         # JSON read/write helpers ("database" layer)
│   ├── excel_processor.py      # Excel -> Pandas -> Validation -> JSON
│   └── logger.py               # Logging (question, tool, output, response)
├── data/
│   ├── products.json           # Sample product catalog
│   ├── orders.json              # Sample customer orders
│   └── tickets.json             # Support tickets (populated at runtime)
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures (isolated temp data)
│   └── test_agent.py            # Unit tests for all tools
├── logs/
│   └── app.log                  # Created automatically at runtime
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Installation

```bash
git clone <your-repo-url> shopmate-ai
cd shopmate-ai

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

---

## 🔑 Environment Setup

ShopMate AI uses **Groq**, not OpenAI.

1. Get a free API key from [console.groq.com/keys](https://console.groq.com/keys).
2. Copy the example env file:

   ```bash
   cp .env.example .env
   ```
3. Edit `.env`:

   ```
   GROQ_API_KEY=your_real_groq_api_key_here
   ```

---

## ▶️ Running Instructions

**Run the Streamlit app:**

```bash
streamlit run app.py
```

Then open the URL Streamlit prints (typically `http://localhost:8501`).

**Run the unit tests:**

```bash
pytest tests/ -v
```

**Check logs** (written automatically while the app runs):

```bash
cat logs/app.log
```

Each log line records the **User Question**, **Selected Tool**, **Tool Output**, and **Final Response** for full traceability.

---

## 💬 Sample Queries

**Shopping Help (chat)**
- `Show running shoes under ₹3000`
- `Recommend wireless earbuds`
- `Compare P101 and P102`
- `What's the cheapest smartwatch you have?`
- `Cheaper alternative to the shoes in order ORD1004`

**My Orders**
- Track Order → `ORD1001`, `ORD1002`, `ORD1003`, `ORD1004`, `ORD1005`
- Cancel / Return / Refund → free-text issue description → returns a ticket like `TKT-1001`

**Admin Mode**
- Upload an `.xlsx` file with columns `id, name, category, brand, price, description, rating, stock`
- View catalog stats and the live ticket inbox

---

## 📸 Screenshots Section

> Add screenshots here after running the app locally.

- `screenshots/customer_welcome.png` — Customer welcome screen
- `screenshots/shopping_help_chat.png` — Shopping Help chat in action
- `screenshots/order_tracking.png` — Track Order result
- `screenshots/ticket_created.png` — Support ticket confirmation
- `screenshots/admin_upload.png` — Admin Excel upload flow
- `screenshots/admin_stats.png` — Catalog statistics dashboard

---

## 🔮 Future Improvements

- Persist conversation history per customer (multi-session memory) using a proper database (Postgres/SQLite) instead of JSON files.
- Add authentication for Admin Mode.
- Add streaming responses in the Streamlit chat for a snappier UX.
- Add a vector store for semantic product search instead of keyword matching.
- Add email/SMS notifications when a ticket is created or resolved.
- Add multi-language support (e.g. Hinglish) for the chat assistant.
- Add automated CI (GitHub Actions) to run `pytest` on every push.
- Add ticket status updates (Open → In Progress → Resolved) from Admin Mode.

---

## 🧰 Tech Stack Summary

- **Python** — core application logic
- **LangGraph** — explicit ReAct agent workflow (`StateGraph`, conditional edges)
- **LangChain** — `@tool` decorators, message types
- **Groq API (`ChatGroq`)** — LLM inference, model `llama-3.3-70b-versatile`
- **Streamlit** — Customer + Admin UI
- **Pandas** — Excel ingestion and validation for Admin catalog uploads
- **JSON files** — lightweight database for products, orders, and tickets
- **Pytest** — unit tests for all tools
