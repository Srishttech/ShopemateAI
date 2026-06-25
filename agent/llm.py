"""
LLM factory for ShopMate AI.

Uses ChatGroq exclusively (model: llama-3.3-70b-versatile).
The API key is read from the GROQ_API_KEY environment variable.
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"


def get_llm(temperature: float = 0.2) -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. Create a .env file (see .env.example) "
            "and set GROQ_API_KEY=your_key_here."
        )
    return ChatGroq(
        model=GROQ_MODEL,
        temperature=temperature,
        api_key=api_key,
        # Llama models on Groq occasionally emit a malformed function-call
        # string when asked to consider multiple tool calls at once
        # (surfaces as a 400 "tool_use_failed" error). Forcing one tool
        # call at a time noticeably reduces how often that happens.
        model_kwargs={"parallel_tool_calls": False},
    )
