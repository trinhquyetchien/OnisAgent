"""Transaction categorization agent."""

from src.agents.base_agent import build_agent

SYSTEM_PROMPT = """\
Bạn là agent phân loại giao dịch của Onis.
Trích xuất mô tả, số tiền, ngày, loại giao dịch (income hoặc expense) và danh mục.
Chỉ trả về dữ liệu có cấu trúc; không tự suy đoán thông tin còn thiếu.
"""


def create_agent():
    """Create the transaction categorization agent."""
    return build_agent(SYSTEM_PROMPT)
