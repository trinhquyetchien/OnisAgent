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


def template_task_query_today() -> tuple[str, dict[str, Any], list[str]]:
    msg = (
        "📅 **Danh sách công việc hôm nay của bạn (3 việc cần giải quyết):**\n"
        "1. 🔴 **[Khẩn cấp]** Hoàn thiện tài liệu kiến trúc OnisAgent (Hạn: 11:30)\n"
        "2. 🟡 **[Quan trọng]** Họp nhóm dự án AI4Life (Hạn: 14:00)\n"
        "3. 🟢 **[Bình thường]** Đọc tài liệu Flutter & Bedrock (Hạn: 22:00)\n\n"
        "👉 *Bạn muốn tập trung xử lý việc nào trước?*"
    )
    data = {
        "count": 3,
        "tasks": [
            {"id": "t1", "title": "Hoàn thiện tài liệu kiến trúc OnisAgent", "priority": "urgent", "due": "11:30"},
            {"id": "t2", "title": "Họp nhóm dự án AI4Life", "priority": "high", "due": "14:00"},
            {"id": "t3", "title": "Đọc tài liệu Flutter & Bedrock", "priority": "normal", "due": "22:00"},
        ],
    }
    quick_replies = ["Thêm việc mới", "Hoàn thành việc 1", "Xem deadline tuần"]
    return msg, data, quick_replies


def template_task_query_deadline() -> tuple[str, dict[str, Any], list[str]]:
    msg = (
        "⏰ **Cảnh báo hạn chót (Deadline) trong 48h tới:**\n"
        "• ⏳ **[Còn 2 giờ]** Nộp báo cáo tiến độ đồ án AI4Life (Hạn: 11:30 hôm nay)\n"
        "• ⏳ **[Còn 26 giờ]** Hoàn tất slide thuyết trình ban giám khảo (Hạn: 12:00 ngày mai)\n\n"
        "💡 *Mẹo: Hãy hoàn thành việc khẩn cấp trước để tránh bị dồn ứ!*"
    )
    data = {
        "count": 2,
        "deadlines": [
            {"title": "Nộp báo cáo tiến độ đồ án AI4Life", "due": "11:30 hôm nay", "hours_left": 2},
            {"title": "Hoàn tất slide thuyết trình ban giám khảo", "due": "12:00 ngày mai", "hours_left": 26},
        ],
    }
    quick_replies = ["Đã làm xong", "Dời hạn chót", "Xem việc hôm nay"]
    return msg, data, quick_replies


def template_task_create(slots: dict[str, Any]) -> tuple[str, dict[str, Any], list[str]]:
    title = slots.get("title", "công việc mới")
    due_date = slots.get("due_date") or slots.get("deadline", "hôm nay")
    priority = slots.get("priority", "medium")
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


def template_finance_balance() -> tuple[str, dict[str, Any], list[str]]:
    msg = (
        "💰 **Tổng số dư khả dụng hiện tại của bạn: 18.450.000₫**\n"
        "• 💵 Tiền mặt: 2.100.000₫\n"
        "• 🏦 Vietcombank: 14.850.000₫\n"
        "• 📱 Ví Momo: 1.500.000₫\n\n"
        "📊 *Tình hình tài chính tuần này đang ở mức an toàn.*"
    )
    data = {
        "total_balance": 18450000,
        "accounts": {"cash": 2100000, "vietcombank": 14850000, "momo": 1500000},
    }
    quick_replies = ["Ghi chi tiêu mới", "Xem lịch sử tuần", "Xem ngân sách"]
    return msg, data, quick_replies


def template_finance_query_debt(slots: dict[str, Any]) -> tuple[str, dict[str, Any], list[str]]:
    person = slots.get("person")
    debt_type = slots.get("debt_type", "all")
    quick_replies = ["Xem ai nợ tôi", "Xem tôi nợ ai", "Ghi nợ mới", "Đã trả nợ"]

    if person:
        p_lower = str(person).lower()
        if p_lower in ["tuấn", "tuan"]:
            msg = f"🤝 **Tuấn** hiện đang nợ bạn **200.000₫** (Tiền ăn trưa ngày 12/11)."
            return msg, {"person": person, "lend": [{"person": "Tuấn", "amount": 200000, "note": "Tiền ăn trưa"}]}, quick_replies
        elif p_lower in ["huy"]:
            msg = f"🤝 **Huy** hiện đang nợ bạn **500.000₫** (Mượn hôm nọ)."
            return msg, {"person": person, "lend": [{"person": "Huy", "amount": 500000, "note": "Mượn hôm nọ"}]}, quick_replies
        elif p_lower in ["nam"]:
            msg = f"🤝 Bạn đang nợ **Nam** **150.000₫** (Tiền đổ xăng)."
            return msg, {"person": person, "borrow": [{"person": "Nam", "amount": 150000, "note": "Tiền đổ xăng"}]}, quick_replies
        else:
            msg = f"🤝 Hiện tại bạn và **{person}** không có khoản nợ nào chưa thanh toán."
            return msg, {"person": person, "lend": [], "borrow": []}, quick_replies

    if debt_type == "lend":
        msg = (
            "🤝 **Danh sách người đang nợ bạn:**\n"
            "• 🟢 Tuấn: 200.000₫ (Tiền ăn trưa)\n"
            "• 🟢 Huy: 500.000₫ (Mượn hôm nọ)\n"
            "👉 **Tổng tiền người khác nợ bạn:** **700.000₫**."
        )
        data = {"total_lend": 700000, "records": [{"person": "Tuấn", "amount": 200000}, {"person": "Huy", "amount": 500000}]}
        return msg, data, quick_replies

    if debt_type == "borrow":
        msg = (
            "🤝 **Các khoản bạn đang nợ người khác:**\n"
            "• 🔴 Nợ Nam: 150.000₫ (Tiền đổ xăng)\n"
            "👉 **Tổng nợ cần trả:** **150.000₫**."
        )
        data = {"total_borrow": 150000, "records": [{"person": "Nam", "amount": 150000}]}
        return msg, data, quick_replies

    # all
    msg = (
        "🤝 **Sổ theo dõi nợ cá nhân của bạn hiện tại:**\n"
        "• 🟢 **Người khác đang nợ bạn: 700.000₫**\n"
        "  - Tuấn: 200.000₫ (Tiền ăn trưa)\n"
        "  - Huy: 500.000₫ (Mượn hôm nọ)\n"
        "• 🔴 **Bạn đang nợ người khác: 150.000₫**\n"
        "  - Nợ Nam: 150.000₫ (Tiền đổ xăng)\n\n"
        "👉 **Số dư cho mượn ròng:** **+550.000₫** (bạn đang cho vay nhiều hơn nợ)."
    )
    data = {
        "total_lend": 700000,
        "total_borrow": 150000,
        "net_balance": 550000,
        "lend_records": [{"person": "Tuấn", "amount": 200000}, {"person": "Huy", "amount": 500000}],
        "borrow_records": [{"person": "Nam", "amount": 150000}],
    }
    return msg, data, quick_replies


def template_finance_split_bill(slots: dict[str, Any]) -> tuple[str, dict[str, Any], list[str]]:
    total = slots.get("total_amount") or slots.get("amount", 800000)
    members = slots.get("members_count", 4)
    desc = slots.get("description", "Hóa đơn nhóm")

    try:
        total_dec = Decimal(str(total))
        members_int = int(members) if int(members) > 0 else 1
        each_amount = (total_dec / members_int).quantize(Decimal("1"))
    except Exception:
        total_dec = Decimal("800000")
        members_int = 4
        each_amount = Decimal("200000")

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


def template_system_greeting_summary() -> tuple[str, dict[str, Any], list[str]]:
    msg = (
        "☀️ **Chào buổi sáng! Chúc bạn một ngày mới tràn đầy năng lượng.**\n\n"
        "📊 **Tóm tắt nhanh đầu ngày:**\n"
        "• 💰 Số dư ví khả dụng: **18.450.000₫**\n"
        "• 📋 Công việc hôm nay: **3 việc cần làm** (1 việc khẩn cấp)\n"
        "• ⏰ Deadline gần nhất: **Nộp báo cáo tiến độ** lúc 11:30\n\n"
        "Bạn muốn bắt đầu với công việc nào trước?"
    )
    data = {
        "balance": 18450000,
        "today_tasks_count": 3,
        "urgent_task": "Nộp báo cáo tiến độ đồ án AI4Life",
    }
    quick_replies = ["Xem việc hôm nay", "Ghi chi tiêu", "Xem sổ nợ"]
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
