import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple
from . import db
from .config import CONFIDENCE_THRESHOLD
from .kev_client import evaluate_system1
from .ollama_client import generate_reasoning, get_active_model
from .tools import FinanceTools, TaskTools, SavingsTools, ReminderTools, MemoryTools


def parse_amount(text: str) -> Optional[float]:
    raw = text.lower()
    # Match triệu (e.g. 15 triệu, 1.5 triệu, 15tr)
    m_trieu = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:triệu|tr|củ)\b", raw)
    if m_trieu:
        val = float(m_trieu.group(1).replace(",", "."))
        return val * 1_000_000

    # Match nghìn / k (e.g. 23 nghìn, 23k, 23.000, 150k)
    m_k = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:nghìn|ngàn|k)\b", raw)
    if m_k:
        val = float(m_k.group(1).replace(",", "."))
        return val * 1_000

    # Match raw digits with thousand dots (e.g. 23.000, 150.000, 15.000.000)
    m_dot = re.search(r"\b(\d{1,3}(?:\.\d{3})+)\b", raw)
    if m_dot:
        val_str = m_dot.group(1).replace(".", "")
        return float(val_str)

    # Match standalone numbers
    m_num = re.search(r"\b(\d+)\s*(?:đồng|đ|vnd)?\b", raw)
    if m_num:
        val = float(m_num.group(1))
        # If user writes "23 đồng" but means 23k, check if < 1000 and context suggests thousands
        return val

    return None


def extract_category_and_desc(text: str, tx_type: str = "expense") -> Tuple[str, str]:
    raw = text.lower()
    desc = text.strip()
    
    # Strip trigger words
    clean = re.sub(r"^(tôi|mình|vừa)?\s*(chi|tiêu|mua|thu|nhận|vừa chi|đã chi)\s*", "", raw)
    # Strip amount
    clean = re.sub(r"(\d+(?:[.,]\d+)?)\s*(triệu|tr|củ|nghìn|ngàn|k|đồng|đ|vnd)?", "", clean).strip()
    clean = re.sub(r"^(tiền|cho)?\s*", "", clean).strip()
    if clean:
        desc = clean.capitalize()

    if any(w in raw for w in ["nước", "điện", "tiện ích", "internet", "wifi"]):
        return "Hóa đơn & Tiện ích", desc or "Tiện ích & Hóa đơn"
    if any(w in raw for w in ["cơm", "phở", "ăn", "uống", "trà sữa", "cà phê", "bún", "bánh"]):
        return "Ăn uống", desc or "Ăn uống"
    if any(w in raw for w in ["xăng", "xe", "grab", "taxi", "vé", "đi lại", "gửi xe"]):
        return "Đi lại", desc or "Đi lại"
    if any(w in raw for w in ["sách", "học", "khóa học", "kotlin", "python", "lập trình", "thi"]):
        return "Học tập & Phát triển", desc or "Học tập"
    if any(w in raw for w in ["lương", "thưởng", "thù lao", "hoa hồng"]):
        return "Lương", desc or "Tiền lương"
        
    return "Khác", desc or ("Khoản chi tiêu" if tx_type == "expense" else "Khoản thu nhập")


def extract_task_info(text: str) -> Tuple[str, Optional[str], str]:
    raw = text.lower()
    title = text.strip()
    
    # Priority
    priority = "medium"
    if any(w in raw for w in ["gấp", "quan trọng", "high", "khẩn cấp"]):
        priority = "high"
    elif any(w in raw for w in ["thong thả", "khi nào rảnh", "low", "thấp"]):
        priority = "low"
        
    # Deadline
    deadline = None
    now = datetime.now()
    if "tối mai" in raw or "ngày mai" in raw:
        tomorrow = now + timedelta(days=1)
        if "8 giờ tối" in raw or "20h" in raw or "20:00" in raw:
            deadline = tomorrow.replace(hour=20, minute=0, second=0).isoformat(timespec="seconds")
        elif "sáng mai" in raw or "9h" in raw:
            deadline = tomorrow.replace(hour=9, minute=0, second=0).isoformat(timespec="seconds")
        else:
            deadline = tomorrow.replace(hour=18, minute=0, second=0).isoformat(timespec="seconds")
    elif "hôm nay" in raw:
        deadline = now.replace(hour=21, minute=0, second=0).isoformat(timespec="seconds")
    elif "thứ 6" in raw or "thứ sáu" in raw:
        # compute next Friday
        days_ahead = (4 - now.weekday() + 7) % 7
        if days_ahead == 0:
            days_ahead = 7
        target = now + timedelta(days=days_ahead)
        deadline = target.replace(hour=17, minute=0, second=0).isoformat(timespec="seconds")
        
    # Clean task title
    clean_title = re.sub(r"^(thêm task|tạo task|thêm việc|cần làm|nhắc tôi)\s*", "", raw)
    # Remove deadline phrases
    clean_title = re.sub(r"(lúc \d+\s*(giờ|h)( tối| sáng)?( mai)?|tối mai|ngày mai|hôm nay|thứ 6|thứ sáu)", "", clean_title)
    clean_title = re.sub(r"(mức ưu tiên \w+|gấp|quan trọng)", "", clean_title).strip()
    if clean_title:
        title = clean_title.capitalize()
        
    return title, deadline, priority


async def process_user_request(text: str) -> Dict[str, Any]:
    """
    Main orchestration router:
    1. Evaluates System 1 with Kev decision model.
    2. Dispatches via Fast Path (direct tool + template) OR Reasoning Path (Ollama LLM).
    3. Guarantees safety and logs activity into temporary JSON storage.
    """
    # 1. System 1 Evaluation via Kev
    sys1_res = await evaluate_system1(text)
    answers = sys1_res.get("answers", {})
    
    intent_ans = answers.get("intent", {})
    intent = intent_ans.get("choice", "agent.unknown")
    confidence = intent_ans.get("confidence", 0.5)
    
    comp_ans = answers.get("complexity", {})
    complexity = comp_ans.get("choice", "simple")
    
    risk_ans = answers.get("risk", {})
    risk = risk_ans.get("choice", "read")
    
    sys1_latency = sys1_res.get("latency_ms", 10.0)
    
    response_payload: Dict[str, Any] = {
        "text": text,
        "reply": "",
        "path": "fast_path",
        "sys1": {
            "model": sys1_res.get("model", "Kev Decision Model"),
            "backend": sys1_res.get("backend", "embedded"),
            "intent": intent,
            "confidence": confidence,
            "complexity": complexity,
            "risk": risk,
            "latency_ms": sys1_latency,
            "probabilities": intent_ans.get("probabilities", {})
        },
        "llm": None,
        "tool_result": None
    }
    
    # 2. Routing Decision
    # If high risk (e.g., delete all) -> safety check
    if risk == "write_high":
        response_payload["reply"] = (
            "⚠️ **Cảnh báo an toàn dữ liệu (Policy Engine):** "
            "Thao tác này có rủi ro cao đối với dữ liệu tài chính của bạn. "
            "Vui lòng vào tab 'Dữ liệu JSON' nếu bạn thực sự muốn reset hoặc xóa cơ sở dữ liệu."
        )
        db.add_activity_log(text, "policy_blocked", intent, confidence, sys1_latency, status="blocked")
        return response_payload

    # Fast Path Execution: Intent is clear, simple complexity, confidence adequate
    if complexity == "simple" and confidence >= CONFIDENCE_THRESHOLD:
        response_payload["path"] = "fast_path"
        
        if intent == "transaction.create_expense":
            amount = parse_amount(text)
            if not amount or amount <= 0:
                response_payload["reply"] = "Tôi nhận thấy bạn muốn ghi nhận khoản chi tiêu, nhưng chưa rõ số tiền. Bạn có thể cho tôi biết số tiền cụ thể không (ví dụ: 'Chi 35k tiền trà sữa')?"
            else:
                category, desc = extract_category_and_desc(text, tx_type="expense")
                res = FinanceTools.create_expense(amount, category, desc)
                response_payload["tool_result"] = res
                response_payload["reply"] = f"⚡ **[System 1 Fast Path]** {res['message']}"

        elif intent == "transaction.create_income":
            amount = parse_amount(text)
            if not amount or amount <= 0:
                response_payload["reply"] = "Tôi nhận diện bạn muốn ghi nhận thu nhập. Vui lòng cho biết số tiền cụ thể (ví dụ: 'Nhận lương 15 triệu')."
            else:
                category, desc = extract_category_and_desc(text, tx_type="income")
                res = FinanceTools.create_income(amount, category, desc)
                response_payload["tool_result"] = res
                response_payload["reply"] = f"⚡ **[System 1 Fast Path]** {res['message']}"

        elif intent == "transaction.query":
            res = FinanceTools.get_transactions(limit=5)
            txs = res.get("transactions", [])
            lines = [f"⚡ **[System 1 Fast Path]** 5 giao dịch gần nhất của bạn:"]
            for t in txs:
                sign = "-" if t["type"] == "expense" else "+"
                lines.append(f"• `{t['date'][:10]}`: {sign}{t['amount']:,.0f} đ ({t['category']}) - *{t['description']}*")
            response_payload["reply"] = "\n".join(lines)
            response_payload["tool_result"] = res

        elif intent in ["finance.summary", "budget.query"]:
            res = FinanceTools.get_summary()
            data = res.get("data", {})
            response_payload["reply"] = (
                f"⚡ **[System 1 Fast Path] Tổng kết tài chính hiện tại:**\n"
                f"• **Số dư:** `{data['balance']:,.0f} đ`\n"
                f"• **Tổng thu:** `{data['total_income']:,.0f} đ`\n"
                f"• **Tổng chi:** `{data['total_expense']:,.0f} đ`\n"
                f"• **Hạn mức tháng:** `{data['monthly_limit']:,.0f} đ` (Đã dùng: {data['percent_budget']}%)"
            )
            response_payload["tool_result"] = res

        elif intent == "task.create":
            title, deadline, priority = extract_task_info(text)
            res = TaskTools.create_task(title, deadline, priority)
            response_payload["tool_result"] = res
            response_payload["reply"] = f"⚡ **[System 1 Fast Path]** {res['message']}"

        elif intent == "task.complete":
            # Extract task keyword
            kw = re.sub(r"\b(xong|hoàn thành|complete|làm xong|đã xong|task|việc)\b", "", text.lower()).strip()
            res = TaskTools.complete_task(kw or text)
            response_payload["tool_result"] = res
            if res.get("success"):
                response_payload["reply"] = f"⚡ **[System 1 Fast Path]** {res['message']}"
            else:
                response_payload["reply"] = f"⚠️ {res.get('error', 'Không tìm thấy nhiệm vụ phù hợp.')}"

        elif intent == "task.query":
            res = TaskTools.get_tasks()
            tasks = res.get("tasks", [])
            pending = [t for t in tasks if t.get("status") == "pending"]
            lines = [f"⚡ **[System 1 Fast Path]** Bạn có **{len(pending)}** việc cần làm:"]
            for t in pending[:5]:
                dl = f" (Hạn: {t['deadline'][:16]})" if t.get("deadline") else ""
                lines.append(f"• `[{t['priority'].upper()}]` {t['title']}{dl}")
            if not pending:
                lines.append("• Hiện tại bạn không có việc nào còn tồn đọng. Tuyệt vời!")
            response_payload["reply"] = "\n".join(lines)
            response_payload["tool_result"] = res

        elif intent == "task.delete":
            kw = re.sub(r"\b(xóa task|xóa việc|hủy task|hủy việc|bỏ task|task|việc)\b", "", text.lower()).strip()
            res = TaskTools.delete_task(kw or text)
            response_payload["tool_result"] = res
            response_payload["reply"] = f"⚡ **[System 1 Fast Path]** {res.get('message') or res.get('error')}"

        elif intent == "budget.set":
            amt = parse_amount(text)
            if amt and amt > 0:
                res = FinanceTools.set_monthly_budget(amt)
                response_payload["tool_result"] = res
                response_payload["reply"] = f"⚡ **[System 1 Fast Path]** {res['message']}"
            else:
                response_payload["reply"] = "Vui lòng cung cấp số tiền hạn mức ngân sách hợp lệ (ví dụ: 'Đặt ngân sách 10 triệu')."

        elif intent == "savings.goal":
            amt = parse_amount(text)
            raw_l = text.lower()
            if any(w in raw_l for w in ["nạp", "bỏ heo", "thêm tiền", "cộng"]):
                # Deposit
                kw = re.sub(r"\b(nạp|bỏ heo|thêm tiền|vào|quỹ|mục tiêu)\b", "", raw_l)
                kw = re.sub(r"(\d+[\.,]?\d*|\d+)\s*(k|nghìn|ngàn|triệu|đ|vnd)?", "", kw).strip()
                res = SavingsTools.deposit(kw or "tiết kiệm", amt or 0)
                response_payload["tool_result"] = res
                response_payload["reply"] = f"⚡ **[System 1 Fast Path]** {res.get('message') or res.get('error')}"
            else:
                # Add goal
                goal_name = re.sub(r"^(tạo mục tiêu|tiết kiệm|mục tiêu|lập quỹ)\s*", "", text, flags=re.IGNORECASE)
                goal_name = re.sub(r"(\d+[\.,]?\d*|\d+)\s*(k|nghìn|ngàn|triệu|đ|vnd|đồng)?", "", goal_name).strip()
                res = SavingsTools.add_goal(goal_name or "Mục tiêu tiết kiệm mới", amt or 10000000)
                response_payload["tool_result"] = res
                response_payload["reply"] = f"⚡ **[System 1 Fast Path]** {res['message']}"

        elif intent == "finance.loan":
            # Extract principal (e.g. 50 triệu), annual rate (e.g. 10%), months (e.g. 12 tháng)
            amt = parse_amount(text) or 50000000
            m_months = re.search(r"(\d+)\s*(?:tháng|thg)\b", text.lower())
            months = int(m_months.group(1)) if m_months else 12
            m_rate = re.search(r"(\d+(?:[.,]\d+)?)\s*%", text.lower())
            rate = float(m_rate.group(1).replace(",", ".")) if m_rate else 10.0
            res = FinanceTools.calculate_loan(amt, rate, months)
            response_payload["tool_result"] = res
            response_payload["reply"] = f"⚡ **[System 1 Fast Path - Công cụ tính toán tài chính]** {res['message']}"

        elif intent == "reminder.create":
            clean_text = re.sub(r"^(nhắc tôi|lời nhắc|nhắc nhở|hẹn giờ)\s*", "", text, flags=re.IGNORECASE).strip()
            _, dl, _ = extract_task_info(text)
            res = ReminderTools.create_reminder(clean_text or text, dl)
            response_payload["tool_result"] = res
            response_payload["reply"] = f"⚡ **[System 1 Fast Path]** {res['message']}"

        elif intent == "memory.note":
            content = re.sub(r"^(ghi nhớ|nhớ là|sở thích|lưu ý là)\s*", "", text, flags=re.IGNORECASE).strip()
            res = MemoryTools.save_note(content or text)
            response_payload["tool_result"] = res
            response_payload["reply"] = f"⚡ **[System 1 Fast Path - Memory Tool]** {res['message']}"

        # Log fast path execution
        db.add_activity_log(text, "system1", intent, confidence, sys1_latency, status="success")
        return response_payload

    # 3. Reasoning Path Execution (LLM via Ollama)
    response_payload["path"] = "reasoning_path"
    
    # Fetch real live data from JSON DB to give grounded context to LLM
    fin_summary = db.get_finance_summary()
    recent_txs = db.get_transactions()[:8]
    active_tasks = [t for t in db.get_tasks() if t.get("status") == "pending"]
    
    llm_context = {
        "finance_summary": fin_summary,
        "recent_transactions": [
            {"type": t["type"], "amount": t["amount"], "category": t["category"], "desc": t["description"], "date": t["date"][:10]}
            for t in recent_txs
        ],
        "pending_tasks": [
            {"title": t["title"], "deadline": t.get("deadline"), "priority": t["priority"]}
            for t in active_tasks
        ]
    }
    
    # Specific prompt guidance depending on intent
    custom_prompt = None
    if intent == "finance.analyze_spending":
        custom_prompt = (
            "Bạn là OnisAgent, phụ trách phân tích chi tiêu tài chính chuyên sâu. "
            "Dựa trên các giao dịch thực tế và hạn mức ngân sách được cung cấp trong context, hãy chỉ ra danh mục chi nhiều nhất, "
            "so sánh với hạn mức tháng, đánh giá xem có bất thường hay không và đưa ra 2-3 gợi ý hành động cụ thể để tiết kiệm."
        )
    elif intent == "work.plan_day":
        custom_prompt = (
            "Bạn là OnisAgent, phụ trách trợ lý lập kế hoạch công việc hàng ngày. "
            "Dựa vào danh sách các nhiệm vụ đang chờ (pending tasks) cùng mức độ ưu tiên và deadline trong context, hãy thiết lập một lịch trình làm việc tối ưu cho hôm nay. "
            "Nêu rõ thứ tự thực hiện theo ma trận khẩn cấp/quan trọng và đề xuất khung giờ gợi ý."
        )

    llm_res = await generate_reasoning(text, context_data=llm_context, custom_system_prompt=custom_prompt)
    
    response_payload["llm"] = {
        "model": llm_res.get("model", get_active_model()),
        "latency_ms": llm_res.get("latency_ms", 0),
        "eval_count": llm_res.get("eval_count", 0),
        "prompt_eval_count": llm_res.get("prompt_eval_count", 0)
    }
    
    response_payload["reply"] = f"🧠 **[LLM Reasoning Path - {get_active_model()}]**\n\n{llm_res.get('text', '')}"
    
    # Log reasoning path
    db.add_activity_log(text, f"llm_{get_active_model()}", intent, confidence, llm_res.get("latency_ms", 0), status="success" if llm_res.get("success") else "error")
    return response_payload
