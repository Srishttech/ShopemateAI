"""
LangGraph ReAct workflow for ShopMate AI.

    START
      |
      v
   [agent]  <-------------------+
      |  (tool_calls?)          |
      | yes            no       |
      v                |        |
   [tools]              v       |
      |                END      |
      +------------------------>+

The agent node calls ChatGroq (bound with all tools). If the model
responds with tool_calls, we route to the tools node, execute the
requested tool(s) against our JSON "database", feed the results back
to the agent as ToolMessages, and loop until the model is ready to
give a final answer (no more tool_calls) -> END.

This loop is what allows the agent to CHAIN tools, e.g. for
"cheaper alternative to the shoes I ordered" it may call get_order()
first and then search_products() with the discovered category/price.
"""

import time
from typing import Annotated, TypedDict

from groq import BadRequestError
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from agent.llm import get_llm
from agent.tools import ALL_TOOLS
from utils.logger import get_logger

logger = get_logger(__name__)

# Groq's hosted Llama models occasionally emit a malformed function-call
# string instead of a valid tool call (surfaces as a 400 error with
# code "tool_use_failed"). This is a known, intermittent generation issue
# on Groq's side, not a problem with our tools or prompt - retrying the
# same request almost always succeeds. We retry a couple of times before
# giving the customer a graceful fallback message instead of crashing.
MAX_TOOL_CALL_RETRIES = 2
RETRY_BACKOFF_SECONDS = 0.8

FALLBACK_REPLY = (
    "Sorry, I had a little trouble understanding that request just now. "
    "Could you try rephrasing it - for example mentioning the product, "
    "category, budget, or order ID a bit more directly?"
)

SYSTEM_PROMPT = """You are Meera, the friendly shopping assistant for ShopMate AI, an online store.

You can help with:
- Product search (e.g. "show running shoes under ₹3000")
- Product recommendations (e.g. "recommend wireless earbuds")
- Product comparisons (use get_product for each item, then compare price/rating/features)
- Cheaper alternatives (if the customer refers to something they ordered, first use get_order
  to find out what they bought, then use search_products to find similar, cheaper items)
- Order tracking (use get_order)
- Creating support tickets for cancellations, returns, and refund issues (use create_ticket)
 
STRICT RULES - follow these exactly:
1. NEVER invent or guess product names, prices, stock, order details, or ticket numbers.
   Only state facts that came from a tool result.
2. Always use a tool before answering questions about products, orders, or tickets.
3. If a tool result starts with NOT_FOUND, NO_RESULTS, or EMPTY_QUERY, tell the customer
   honestly and clearly, and ask a helpful follow-up question (e.g. ask for the correct
   order ID, or a different search term/budget). Do not pretend something exists.
4. When you create a support ticket, always tell the customer their ticket ID exactly as
   returned by the tool (e.g. TKT-1001).
5. Keep replies short, warm, and easy to read. Use ₹ for prices. Use bullet points when
   listing multiple products.
6. If a request is ambiguous, ask a brief clarifying question instead of guessing.
"""


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def _is_tool_use_failed(exc: BadRequestError) -> bool:
    """Detect Groq's intermittent 'malformed function call' error."""
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        code = body.get("error", {}).get("code", "")
        if code == "tool_use_failed":
            return True
    return "tool_use_failed" in str(exc)


def _invoke_with_retry(llm_with_tools, messages):
    """Call the LLM, retrying on Groq's tool_use_failed generation error.

    Any other error (auth, rate limit, network, etc.) is raised immediately -
    we only retry the specific intermittent failure mode described above.
    """
    last_exc = None
    for attempt in range(MAX_TOOL_CALL_RETRIES + 1):
        try:
            return llm_with_tools.invoke(messages)
        except BadRequestError as exc:
            last_exc = exc
            if _is_tool_use_failed(exc) and attempt < MAX_TOOL_CALL_RETRIES:
                logger.warning(
                    "Groq tool_use_failed (malformed function call) - retrying %s/%s",
                    attempt + 1, MAX_TOOL_CALL_RETRIES,
                )
                time.sleep(RETRY_BACKOFF_SECONDS)
                continue
            raise
    raise last_exc  # pragma: no cover - loop always returns or raises above


def _agent_node_factory(llm_with_tools):
    def agent_node(state: AgentState):
        messages = state["messages"]
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

        last_user_msg = next(
            (m.content for m in reversed(messages) if m.__class__.__name__ == "HumanMessage"),
            "",
        )
        logger.info("USER_QUESTION -> %s", last_user_msg)

        try:
            response = _invoke_with_retry(llm_with_tools, messages)
        except BadRequestError as exc:
            # Retries exhausted - don't crash the Streamlit app, give the
            # customer an honest, friendly message instead.
            logger.error("Groq tool_use_failed persisted after retries: %s", exc)
            response = AIMessage(content=FALLBACK_REPLY)

        tool_calls = getattr(response, "tool_calls", None)
        if tool_calls:
            logger.info("SELECTED_TOOL -> %s", [tc["name"] for tc in tool_calls])
        else:
            logger.info("FINAL_RESPONSE -> %s", response.content)

        return {"messages": [response]}

    return agent_node


def _tool_node(state: AgentState):
    """Custom tool-execution node (instead of the prebuilt ToolNode) so we
    can explicitly log every tool's output, per the project's logging spec."""
    tool_map = {t.name: t for t in ALL_TOOLS}
    last_message = state["messages"][-1]
    outputs = []

    for call in getattr(last_message, "tool_calls", []) or []:
        tool_fn = tool_map.get(call["name"])
        if tool_fn is None:
            result = f"ERROR: Unknown tool '{call['name']}'."
        else:
            try:
                result = tool_fn.invoke(call["args"])
            except Exception as exc:  # noqa: BLE001
                result = f"ERROR: Tool '{call['name']}' failed: {exc}"

        logger.info("TOOL_OUTPUT [%s] -> %s", call["name"], str(result)[:500])

        outputs.append(
            ToolMessage(content=str(result), tool_call_id=call["id"], name=call["name"])
        )

    return {"messages": outputs}


def _route_after_agent(state: AgentState):
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return END


def build_graph():
    """Compile and return the LangGraph ReAct agent."""
    llm = get_llm()
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    graph = StateGraph(AgentState)
    graph.add_node("agent", _agent_node_factory(llm_with_tools))
    graph.add_node("tools", _tool_node)

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", _route_after_agent, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


# Module-level singleton so Streamlit doesn't rebuild the graph on every rerun.
_compiled_graph = None


def get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph
