"""Pure-Python financial calculations using decimal arithmetic."""

from decimal import Decimal, InvalidOperation
from typing import Any


def _amount(value: Any) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid transaction amount: {value!r}") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError(f"Transaction amount must be finite and non-negative: {value!r}")
    return amount


def summarize_transactions(transactions: list[dict[str, Any]]) -> dict[str, Decimal]:
    """Return income, expenses, and balance for income/expense transactions."""
    income = Decimal("0")
    expenses = Decimal("0")
    for transaction in transactions:
        amount = _amount(transaction["amount"])
        transaction_type = transaction["type"].strip().lower()
        if transaction_type == "income":
            income += amount
        elif transaction_type == "expense":
            expenses += amount
        else:
            raise ValueError(f"Unsupported transaction type: {transaction_type!r}")
    return {
        "income": income,
        "expenses": expenses,
        "balance": income - expenses,
    }


def expense_ratio(
    expenses: Decimal | int | float | str,
    income: Decimal | int | float | str,
) -> Decimal:
    """Return the expense-to-income percentage (0 when income is zero)."""
    expense_amount = _amount(expenses)
    income_amount = _amount(income)
    if income_amount == 0:
        return Decimal("0")
    return expense_amount / income_amount * Decimal("100")
