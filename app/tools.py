from typing import Any, Dict, List, Optional
from . import db


class PolicyEngine:
    @staticmethod
    def validate_transaction(amount: float, category: str, description: str) -> Optional[str]:
        if amount <= 0:
            return "Số tiền phải lớn hơn 0."
        if amount > 1_000_000_000:
            return "Số tiền vượt quá giới hạn an toàn (tối đa 1 tỷ VND/giao dịch)."
        if not description or len(description.strip()) == 0:
            return "Mô tả giao dịch không được để trống."
        return None

    @staticmethod
    def validate_task(title: str) -> Optional[str]:
        if not title or len(title.strip()) < 2:
            return "Tên nhiệm vụ phải có ít nhất 2 ký tự."
        return None


class FinanceTools:
    @staticmethod
    def create_expense(amount: float, category: str, description: str, created_by: str = "system1_fast_path") -> Dict[str, Any]:
        err = PolicyEngine.validate_transaction(amount, category, description)
        if err:
            return {"success": False, "error": err}
        tx = db.add_transaction("expense", amount, category, description, created_by=created_by)
        summary = db.get_finance_summary()
        return {
            "success": True,
            "transaction": tx,
            "new_balance": summary["balance"],
            "spent_so_far": summary["total_expense"],
            "message": f"Đã ghi nhận khoản chi {amount:,.0f} đ cho '{description}' (danh mục: {category}). Số dư hiện tại: {summary['balance']:,.0f} đ."
        }

    @staticmethod
    def create_income(amount: float, category: str, description: str, created_by: str = "system1_fast_path") -> Dict[str, Any]:
        err = PolicyEngine.validate_transaction(amount, category, description)
        if err:
            return {"success": False, "error": err}
        tx = db.add_transaction("income", amount, category, description, created_by=created_by)
        summary = db.get_finance_summary()
        return {
            "success": True,
            "transaction": tx,
            "new_balance": summary["balance"],
            "message": f"Đã ghi nhận khoản thu {amount:,.0f} đ từ '{description}'. Số dư hiện tại: {summary['balance']:,.0f} đ."
        }

    @staticmethod
    def get_summary() -> Dict[str, Any]:
        summary = db.get_finance_summary()
        return {"success": True, "data": summary}

    @staticmethod
    def get_transactions(limit: int = 10) -> Dict[str, Any]:
        txs = db.get_transactions()[:limit]
        return {"success": True, "transactions": txs, "total_count": len(txs)}

    @staticmethod
    def get_budget() -> Dict[str, Any]:
        db_data = db.load_db()
        budgets = db_data.get("budgets", {})
        summary = db.get_finance_summary()
        return {
            "success": True,
            "budget": budgets,
            "spent": summary["total_expense"],
            "remaining": budgets.get("monthly_limit", 8000000) - summary["total_expense"]
        }

    @staticmethod
    def set_monthly_budget(new_limit: float) -> Dict[str, Any]:
        if new_limit <= 0:
            return {"success": False, "error": "Hạn mức ngân sách phải lớn hơn 0."}
        res = db.set_monthly_budget(new_limit)
        return {
            "success": True,
            "budget": res,
            "message": f"Đã cập nhật hạn mức ngân sách tháng thành {new_limit:,.0f} đ."
        }

    @staticmethod
    def filter_transactions(min_amount: Optional[float] = None, max_amount: Optional[float] = None, category: Optional[str] = None) -> Dict[str, Any]:
        txs = db.filter_transactions(min_amount, max_amount, category)
        return {
            "success": True,
            "count": len(txs),
            "transactions": txs[:15]
        }

    @staticmethod
    def calculate_loan(principal: float, annual_rate_pct: float, months: int) -> Dict[str, Any]:
        """Tính toán lãi suất và tiền trả góp hàng tháng."""
        if principal <= 0 or months <= 0:
            return {"success": False, "error": "Số tiền vay và số tháng phải lớn hơn 0."}
        monthly_rate = (annual_rate_pct / 100) / 12
        if monthly_rate > 0:
            monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
        else:
            monthly_payment = principal / months
        total_payment = monthly_payment * months
        total_interest = total_payment - principal
        return {
            "success": True,
            "principal": principal,
            "annual_rate_pct": annual_rate_pct,
            "months": months,
            "monthly_payment": round(monthly_payment),
            "total_interest": round(total_interest),
            "total_payment": round(total_payment),
            "message": f"Vay {principal:,.0f} đ trong {months} tháng (lãi {annual_rate_pct}%/năm): Mỗi tháng cần trả khoảng {round(monthly_payment):,.0f} đ. Tổng tiền lãi: {round(total_interest):,.0f} đ."
        }


class TaskTools:
    @staticmethod
    def create_task(title: str, deadline: Optional[str] = None, priority: str = "medium") -> Dict[str, Any]:
        err = PolicyEngine.validate_task(title)
        if err:
            return {"success": False, "error": err}
        task = db.add_task(title, deadline, priority)
        return {
            "success": True,
            "task": task,
            "message": f"Đã thêm nhiệm vụ: '{title}'" + (f" (hạn chót: {deadline})" if deadline else "") + f" với mức ưu tiên {priority}."
        }

    @staticmethod
    def complete_task(keyword_or_id: str) -> Dict[str, Any]:
        res = db.toggle_task(keyword_or_id)
        if not res:
            res = db.complete_task_by_title(keyword_or_id)
        if res:
            return {
                "success": True,
                "task": res,
                "message": f"Đã đánh dấu hoàn thành nhiệm vụ: '{res['title']}'."
            }
        return {
            "success": False,
            "error": f"Không tìm thấy nhiệm vụ nào khớp với '{keyword_or_id}'."
        }

    @staticmethod
    def delete_task(keyword_or_id: str) -> Dict[str, Any]:
        success = db.delete_task(keyword_or_id)
        if success:
            return {"success": True, "message": f"Đã xóa nhiệm vụ '{keyword_or_id}'."}
        return {"success": False, "error": f"Không tìm thấy nhiệm vụ nào khớp với '{keyword_or_id}'."}

    @staticmethod
    def update_priority(keyword_or_id: str, priority: str) -> Dict[str, Any]:
        res = db.update_task_priority(keyword_or_id, priority)
        if res:
            return {"success": True, "task": res, "message": f"Đã chuyển mức ưu tiên của '{res['title']}' thành {priority}."}
        return {"success": False, "error": f"Không tìm thấy nhiệm vụ nào khớp với '{keyword_or_id}'."}

    @staticmethod
    def get_tasks(status: Optional[str] = None) -> Dict[str, Any]:
        all_tasks = db.get_tasks()
        if status:
            filtered = [t for t in all_tasks if t.get("status") == status]
        else:
            filtered = all_tasks
        return {
            "success": True,
            "tasks": filtered,
            "pending_count": sum(1 for t in all_tasks if t.get("status") == "pending"),
            "completed_count": sum(1 for t in all_tasks if t.get("status") == "completed")
        }


class SavingsTools:
    @staticmethod
    def add_goal(name: str, target_amount: float, deadline: Optional[str] = None) -> Dict[str, Any]:
        if target_amount <= 0:
            return {"success": False, "error": "Mục tiêu tiết kiệm phải lớn hơn 0."}
        goal = db.add_savings_goal(name, target_amount, deadline)
        return {
            "success": True,
            "goal": goal,
            "message": f"Đã tạo mục tiêu tiết kiệm: '{name}' với số tiền mục tiêu {target_amount:,.0f} đ" + (f" (hạn chót: {deadline})" if deadline else "") + "."
        }

    @staticmethod
    def deposit(goal_keyword_or_id: str, amount: float) -> Dict[str, Any]:
        if amount <= 0:
            return {"success": False, "error": "Số tiền nạp vào quỹ phải lớn hơn 0."}
        goal = db.deposit_savings_goal(goal_keyword_or_id, amount)
        if goal:
            pct = (goal['current_amount'] / goal['target_amount'] * 100) if goal['target_amount'] > 0 else 0
            return {
                "success": True,
                "goal": goal,
                "message": f"Đã thêm {amount:,.0f} đ vào mục tiêu '{goal['name']}'. Tiến độ hiện tại: {goal['current_amount']:,.0f}/{goal['target_amount']:,.0f} đ ({pct:.1f}%)."
            }
        return {"success": False, "error": f"Không tìm thấy mục tiêu tiết kiệm nào khớp với '{goal_keyword_or_id}'."}

    @staticmethod
    def get_goals() -> Dict[str, Any]:
        goals = db.get_savings_goals()
        return {"success": True, "goals": goals}

    @staticmethod
    def delete_goal(goal_id: str) -> Dict[str, Any]:
        success = db.delete_savings_goal(goal_id)
        return {"success": success}


class ReminderTools:
    @staticmethod
    def create_reminder(text: str, remind_at: Optional[str] = None) -> Dict[str, Any]:
        if not text or len(text.strip()) < 2:
            return {"success": False, "error": "Nội dung lời nhắc không được để trống."}
        rem = db.add_reminder(text, remind_at)
        return {
            "success": True,
            "reminder": rem,
            "message": f"Đã tạo lời nhắc: '{text}'" + (f" vào lúc {remind_at}" if remind_at else "") + "."
        }

    @staticmethod
    def get_reminders() -> Dict[str, Any]:
        rems = db.get_reminders()
        return {"success": True, "reminders": rems}

    @staticmethod
    def delete_reminder(rem_id: str) -> Dict[str, Any]:
        success = db.delete_reminder(rem_id)
        return {"success": success}


class MemoryTools:
    @staticmethod
    def save_note(content: str, category: str = "general") -> Dict[str, Any]:
        if not content or len(content.strip()) < 2:
            return {"success": False, "error": "Nội dung ghi chú không được để trống."}
        note = db.add_note(content, category)
        return {
            "success": True,
            "note": note,
            "message": f"Đã ghi nhớ thông tin: '{content}'."
        }

    @staticmethod
    def get_notes() -> Dict[str, Any]:
        notes = db.get_notes()
        return {"success": True, "notes": notes}
