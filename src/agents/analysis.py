"""Cash-flow analysis agent."""

from src.agents.base_agent import build_agent

SYSTEM_PROMPT = """\
Bạn là agent phân tích dòng tiền của Onis.
Giải thích xu hướng và điểm bất thường dựa trên dữ liệu giao dịch được cung cấp.
Không tự tính lại số liệu; nêu rõ khi dữ liệu đầu vào chưa đủ.
"""


def create_agent():
    """Create the transaction analysis agent."""
    return build_agent(SYSTEM_PROMPT)
