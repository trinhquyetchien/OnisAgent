from decimal import Decimal

import pytest

from src.tools.calculator import (
    calculate_loan_amortization,
    expense_ratio,
    summarize_transactions,
)


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


def test_calculate_loan_amortization_exact_match():
    # 50 million VND, 12 months, 10% annual interest rate
    result = calculate_loan_amortization(
        principal="50000000",
        annual_interest_rate="10",
        months=12,
    )
    assert result["principal"] == Decimal("50000000")
    assert result["months"] == 12
    assert result["monthly_payment"] == Decimal("4395794")
    assert result["total_payment"] == Decimal("52749528")
    assert result["total_interest"] == Decimal("2749528")
    assert len(result["schedule"]) == 12
    assert result["schedule"][-1]["remaining_balance"] == Decimal("0")
