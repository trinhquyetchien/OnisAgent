"""Financial advisory agent wired to deterministic calculation tools."""

import json

from strands import tool

from src.agents.base_agent import build_agent
from src.agents.prompts import ADVISORY_SYSTEM_PROMPT as SYSTEM_PROMPT
from src.tools.calculator import summarize_transactions


@tool
def calculate_cash_flow(transactions_json: str) -> dict[str, str]:
    """Calculate exact income, expenses and balance from a JSON transaction list."""
    transactions = json.loads(transactions_json)
    if not isinstance(transactions, list):
        raise ValueError("transactions_json must contain a JSON list.")
    totals = summarize_transactions(transactions)
    return {key: str(value) for key, value in totals.items()}


def create_agent():
    """Create the advisory agent with deterministic cash-flow calculations."""
    return build_agent(SYSTEM_PROMPT, tools=[calculate_cash_flow])
