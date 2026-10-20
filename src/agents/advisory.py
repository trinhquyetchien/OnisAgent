"""Financial advisory agent wired to deterministic calculation tools."""

import json

from strands import tool

from src.agents.base_agent import build_agent
from src.tools.calculator import summarize_transactions

SYSTEM_PROMPT = """\
Bạn là cố vấn tài chính cá nhân của Onis.
Đưa ra gợi ý tài chính dễ hiểu, phân tích xu hướng chi tiêu và hỗ trợ lập kế hoạch tích lũy quỹ tiết kiệm, không thay thế tư vấn chuyên môn.
Khi cần số liệu thu, chi, số dư hoặc lịch trả nợ vay, luôn gọi công cụ tính toán thích hợp.
Không tự bịa hoặc ước lượng các con số tài chính.
"""


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
