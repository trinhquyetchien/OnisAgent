"""Fixed and dynamic response templates for Kev Fast Path Deterministic Intents.

Provides human-crafted, engaging, professional, and zero-LLM responses
with interactive quick-reply action chips for Flutter Web & Mobile.
"""

from decimal import Decimal
from typing import Any


def format_currency(amount: Any) -> str:
    """Format decimal/int/float into standard Vietnamese currency string (e.g. 45.000₫)."""
    try:
        val = int(Decimal(str(amount)))
        return f"{val:,}₫".replace(",", ".")
    except Exception:
        return f"{amount}₫"


def template_task_create(slots: dict[str, Any]) -> tuple[str, dict[str, Any], list[str]]:
    title = slots.get("title", "công việc mới")
    due_date = slots.get("due_date") or slots.get("deadline", "hôm nay")
    priority = slots.get("priority", "medium")
    priority = getattr(priority, "value", priority)
    prio_labels = {"high": "Cao 🔴", "urgent": "Khẩn cấp 🔴", "medium": "Trung bình 🟡", "low": "Thấp 🟢"}
    prio_display = prio_labels.get(str(priority).lower(), str(priority))

    msg = (
        f"✅ Đã tạo thành công công việc: **'{title}'**\n"
        f"• Hạn chót: {due_date}\n"
        f"• Mức độ ưu tiên: {prio_display}"
    )
    data = {"task": slots}
    quick_replies = ["Xem việc hôm nay", "Tạo thêm việc", "Xem deadline"]
    return msg, data, quick_replies


def template_task_complete(slots: dict[str, Any]) -> tuple[str, dict[str, Any], list[str]]:
    title = slots.get("title") or slots.get("task_id", "công việc")
    msg = f"🎉 Chúc mừng bạn đã hoàn thành công việc: **'{title}'**! Năng suất hôm nay thật tuyệt vời!"
    data = {"completed_task": slots}
    quick_replies = ["Xem việc hôm nay", "Xem việc đã xong"]
    return msg, data, quick_replies


def template_finance_split_bill(slots: dict[str, Any]) -> tuple[str, dict[str, Any], list[str]]:
    total = slots.get("total_amount") or slots.get("amount")
    members = slots.get("members_count") or slots.get("participants")
    desc = slots.get("description", "Hóa đơn nhóm")

    if total is None or members is None:
        return (
            "🧾 Vui lòng cho biết tổng hóa đơn và số người cần chia.",
            {"missing": [key for key, value in (("amount", total), ("participants", members)) if value is None]},
            ["Nhập tổng hóa đơn", "Nhập số người"],
        )

    try:
        total_dec = Decimal(str(total))
        members_int = int(members)
        if total_dec <= 0 or members_int <= 0:
            raise ValueError("amount and participant count must be positive")
        each_amount = (total_dec / members_int).quantize(Decimal("1"))
    except Exception:
        return (
            "🧾 Tổng hóa đơn và số người phải là số dương hợp lệ.",
            {"invalid": ["amount", "participants"]},
            ["Nhập lại thông tin", "Hủy"],
        )

    formatted_total = format_currency(total_dec)
    formatted_each = format_currency(each_amount)

    msg = (
        f"🧾 **Kết quả chia hóa đơn '{desc}' (Tổng: {formatted_total} cho {members_int} người):**\n"
        f"👉 **Mỗi người cần đóng:** **{formatted_each}**.\n\n"
        "Bạn có muốn tôi ghi nhận task nhắc thu tiền những người còn lại không?"
    )
    data = {
        "description": desc,
        "total_amount": float(total_dec),
        "members_count": members_int,
        "each_amount": float(each_amount),
    }
    quick_replies = ["Tạo task nhắc thu tiền", "Tôi đã trả hết", "Hủy"]
    return msg, data, quick_replies


def template_finance_pay_bill(slots: dict[str, Any]) -> tuple[str, dict[str, Any], list[str]]:
    bill_type = slots.get("bill_type", "hóa đơn sinh hoạt")
    amount = slots.get("amount", 0)
    formatted_amount = format_currency(amount)
    msg = (
        f"🧾 Đã ghi nhận thanh toán hóa đơn: **{bill_type}** số tiền **{formatted_amount}**. "
        "Hệ thống sẽ tự động nhắc bạn vào kỳ thanh toán tháng sau!"
    )
    data = {"bill": slots}
    quick_replies = ["Xem số dư", "Lịch sử hóa đơn", "Xem việc hôm nay"]
    return msg, data, quick_replies


def template_system_help() -> tuple[str, dict[str, Any], list[str]]:
    msg = (
        "🤖 **Tôi là OnisAgent – Trợ lý AI cá nhân hợp nhất Quản lý Tài chính & Công việc.**\n\n"
        "Bạn có thể ra lệnh bằng giọng nói hoặc gõ text tự nhiên:\n"
        "• 💰 **Tài chính:** 'chi 45k trà sữa', 'số dư momo còn bao nhiêu', 'ai đang nợ tôi', 'chia tiền lẩu 800k cho 4 người'\n"
        "• 📋 **Công việc:** 'hôm nay có việc gì', 'deadline tuần này', 'tạo việc nộp đồ án chiều mai', 'đã làm xong task 1'\n"
        "• ⚡ Phản hồi siêu tốc ~6ms và tính toán chuẩn xác 100%!"
    )
    quick_replies = ["Xem việc hôm nay", "Xem số dư", "Ai đang nợ tôi"]
    return msg, {}, quick_replies
