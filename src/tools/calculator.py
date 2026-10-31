"""Pure-Python financial calculations using decimal arithmetic."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
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


def calculate_loan_amortization(
    principal: Decimal | int | float | str,
    annual_interest_rate: Decimal | int | float | str,
    months: int | str | Decimal,
) -> dict[str, Any]:
    """Calculate loan amortization schedule for reducing balance loan using pure Decimal.

    Args:
        principal: Total loan amount (e.g. 50000000).
        annual_interest_rate: Annual interest rate in percentage (e.g. 10 for 10% per year).
        months: Loan term in months (e.g. 12).

    Returns:
        dict containing:
            - principal (Decimal)
            - annual_rate_percent (Decimal)
            - months (int)
            - monthly_payment (Decimal)
            - total_payment (Decimal)
            - total_interest (Decimal)
            - schedule (list of monthly payments)
    """
    p = _amount(principal)
    if p == 0:
        raise ValueError("Principal must be greater than zero.")

    try:
        rate_val = Decimal(str(annual_interest_rate))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid interest rate: {annual_interest_rate!r}") from exc
    if not rate_val.is_finite() or rate_val < 0:
        raise ValueError(f"Interest rate must be finite and non-negative: {annual_interest_rate!r}")

    # If rate passed as decimal fraction <= 1 and > 0 (e.g. 0.10), convert to percent (10)
    # If rate is already in percent (e.g. 10.0), keep as percent
    if 0 < rate_val <= 1:
        rate_percent = rate_val * Decimal("100")
        rate_fraction = rate_val
    else:
        rate_percent = rate_val
        rate_fraction = rate_val / Decimal("100")

    try:
        m = int(months)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid months term: {months!r}") from exc
    if m <= 0:
        raise ValueError("Loan term in months must be greater than zero.")

    monthly_rate = rate_fraction / Decimal("12")

    if monthly_rate == 0:
        monthly_payment = (p / Decimal(m)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    else:
        factor = (Decimal("1") + monthly_rate) ** m
        raw_pmt = (p * monthly_rate * factor) / (factor - Decimal("1"))
        monthly_payment = raw_pmt.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    schedule = []
    balance = p
    for month_idx in range(1, m + 1):
        interest_payment = (balance * monthly_rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        if month_idx == m:
            principal_payment = balance
            actual_payment = principal_payment + interest_payment
            balance = Decimal("0")
        else:
            principal_payment = monthly_payment - interest_payment
            actual_payment = monthly_payment
            balance -= principal_payment

        schedule.append({
            "month": month_idx,
            "payment": actual_payment,
            "principal": principal_payment,
            "interest": interest_payment,
            "remaining_balance": balance,
        })

    total_payment = sum(
        (item["payment"] for item in schedule),
        start=Decimal("0"),
    )
    total_interest = sum(
        (item["interest"] for item in schedule),
        start=Decimal("0"),
    )

    return {
        "principal": p,
        "annual_rate_percent": rate_percent,
        "months": m,
        "monthly_payment": monthly_payment,
        "total_payment": total_payment,
        "total_interest": total_interest,
        "schedule": schedule,
    }
