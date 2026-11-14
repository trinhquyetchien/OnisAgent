"""AWS Lambda adapter for deterministic cash-flow calculations."""

from typing import Any

from src.tools.calculator import summarize_transactions


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Calculate cash flow for a Lambda event containing transactions."""
    transactions = event.get("transactions")
    if not isinstance(transactions, list):
        raise ValueError("Event must contain a 'transactions' list.")
    totals = summarize_transactions(transactions)
    return {key: str(value) for key, value in totals.items()}
