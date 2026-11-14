"""AWS Lambda adapter for deterministic loan amortization calculations."""

from typing import Any

from src.tools.calculator import calculate_loan_amortization


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Calculate loan amortization schedule for a Lambda event."""
    principal = event.get("principal")
    rate = event.get("annual_interest_rate")
    months = event.get("months")

    if principal is None or rate is None or months is None:
        raise ValueError("Event must contain 'principal', 'annual_interest_rate', and 'months'.")

    result = calculate_loan_amortization(
        principal=principal,
        annual_interest_rate=rate,
        months=months,
    )

    return {
        "principal": str(result["principal"]),
        "annual_rate_percent": str(result["annual_rate_percent"]),
        "months": result["months"],
        "monthly_payment": str(result["monthly_payment"]),
        "total_payment": str(result["total_payment"]),
        "total_interest": str(result["total_interest"]),
        "schedule": [
            {
                "month": item["month"],
                "payment": str(item["payment"]),
                "principal": str(item["principal"]),
                "interest": str(item["interest"]),
                "remaining_balance": str(item["remaining_balance"]),
            }
            for item in result["schedule"]
        ],
    }
