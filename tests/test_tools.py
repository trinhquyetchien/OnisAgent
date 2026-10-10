from decimal import Decimal

import pytest

from src.tools.calculator import expense_ratio, summarize_transactions


def test_summarize_transactions_uses_exact_decimal_totals():
    result = summarize_transactions(
        [
            {"amount": "100.10", "type": "income"},
            {"amount": "25.05", "type": "expense"},
        ]
    )

    assert result == {
        "income": Decimal("100.10"),
        "expenses": Decimal("25.05"),
        "balance": Decimal("75.05"),
    }


@pytest.mark.parametrize("amount", ["-1", "NaN", "Infinity", "not-money"])
def test_summarize_transactions_rejects_invalid_amounts(amount):
    with pytest.raises(ValueError):
        summarize_transactions([{"amount": amount, "type": "expense"}])


def test_summarize_transactions_rejects_unknown_type():
    with pytest.raises(ValueError, match="Unsupported transaction type"):
        summarize_transactions([{"amount": "1", "type": "transfer"}])


def test_expense_ratio_handles_zero_income():
    assert expense_ratio("15", "0") == Decimal("0")
