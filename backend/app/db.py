import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from .config import DATA_FILE

_lock = threading.Lock()

DEFAULT_DB: Dict[str, Any] = {
    "user": {
        "id": "user_demo_01",
        "name": "Nguyễn Văn An",
        "email": "an.nguyen@example.com",
        "currency": "VND"
    },
    "budgets": {
        "month": "2026-10",
        "monthly_limit": 8000000,
        "spent_so_far": 568000,
        "categories": {
            "Ăn uống": 3000000,
            "Đi lại": 1000000,
            "Hóa đơn & Tiện ích": 1000000,
            "Học tập & Phát triển": 2000000,
            "Khác": 1000000
        }
    },
    "transactions": [
        {
            "id": "tx_001",
            "type": "income",
            "amount": 15000000,
            "category": "Lương",
            "description": "Nhận lương tháng 10",
            "date": "2026-10-05T09:00:00",
            "created_by": "system_init"
        },
        {
            "id": "tx_002",
            "type": "expense",
            "amount": 23000,
            "category": "Hóa đơn & Tiện ích",
            "description": "Tiền nước sinh hoạt",
            "date": "2026-10-06T14:30:00",
            "created_by": "system1_fast_path"
        },
        {
            "id": "tx_003",
            "type": "expense",
            "amount": 45000,
            "category": "Ăn uống",
            "description": "Cơm trưa văn phòng",
            "date": "2026-10-08T12:15:00",
            "created_by": "system1_fast_path"
        },
        {
            "id": "tx_004",
            "type": "expense",
            "amount": 150000,
            "category": "Đi lại",
            "description": "Đổ xăng xe máy",
            "date": "2026-10-10T18:00:00",
            "created_by": "system1_fast_path"
        },
        {
            "id": "tx_005",
            "type": "expense",
            "amount": 350000,
            "category": "Học tập & Phát triển",
            "description": "Mua sách thiết kế hệ thống AI",
            "date": "2026-10-12T10:45:00",
            "created_by": "system1_fast_path"
        }
    ],
    "tasks": [
        {
            "id": "task_001",
            "title": "Học Kotlin Jetpack Compose",
            "deadline": "2026-10-14T20:00:00",
            "priority": "high",
            "status": "pending",
            "created_at": "2026-10-12T08:00:00",
            "completed_at": None
        },
        {
            "id": "task_002",
            "title": "Nộp báo cáo tài chính tháng cho team",
            "deadline": "2026-10-16T17:00:00",
            "priority": "high",
            "status": "pending",
            "created_at": "2026-10-12T09:30:00",
            "completed_at": None
        },
        {
            "id": "task_003",
            "title": "Kiểm tra số dư tài khoản tiết kiệm",
            "deadline": "2026-10-15T12:00:00",
            "priority": "medium",
            "status": "pending",
            "created_at": "2026-10-13T07:15:00",
            "completed_at": None
        },
        {
            "id": "task_004",
            "title": "Tập thể dục 30 phút buổi sáng",
            "deadline": "2026-10-13T06:30:00",
            "priority": "low",
            "status": "completed",
            "created_at": "2026-10-13T06:00:00",
            "completed_at": "2026-10-13T06:35:00"
        }
    ],
    "savings_goals": [
        {
            "id": "goal_001",
            "name": "Mua Laptop M4 mới",
            "target_amount": 35000000,
            "current_amount": 15000000,
            "deadline": "2026-12-31",
            "created_at": "2026-10-01T09:00:00"
        },
        {
            "id": "goal_002",
            "name": "Quỹ khẩn cấp dự phòng",
            "target_amount": 24000000,
            "current_amount": 18000000,
            "deadline": "2027-03-31",
            "created_at": "2026-10-01T09:00:00"
        }
    ],
    "reminders": [
        {
            "id": "rem_001",
            "text": "Thanh toán cước Internet sinh hoạt",
            "remind_at": "2026-10-15T19:00:00",
            "status": "pending"
        },
        {
            "id": "rem_002",
            "text": "Uống đủ 2 lít nước mỗi ngày",
            "remind_at": "2026-10-14T08:00:00",
            "status": "pending"
        }
    ],
    "notes": [
        {
            "id": "note_001",
            "content": "Ưu tiên chi tiêu ăn uống dưới 100k mỗi ngày",
            "category": "preference",
            "created_at": "2026-10-10T10:00:00"
        }
    ],
    "activity_logs": []
}


def init_db():
    if not DATA_FILE.exists():
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        save_db(DEFAULT_DB)


def load_db() -> Dict[str, Any]:
    with _lock:
        if not DATA_FILE.exists():
            init_db()
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            changed = False
            for k in ["savings_goals", "reminders", "notes"]:
                if k not in data or not data[k]:
                    data[k] = DEFAULT_DB.get(k, []).copy()
                    changed = True
            if changed:
                with open(DATA_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            return data
        except Exception:
            return DEFAULT_DB.copy()


def save_db(data: Dict[str, Any]):
    with _lock:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Recalculate spent_so_far
        expenses = sum(
            tx["amount"] for tx in data.get("transactions", [])
            if tx.get("type") == "expense"
        )
        if "budgets" in data:
            data["budgets"]["spent_so_far"] = expenses
            
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def get_transactions() -> List[Dict[str, Any]]:
    db = load_db()
    return db.get("transactions", [])


def add_transaction(tx_type: str, amount: float, category: str, description: str, created_by: str = "agent") -> Dict[str, Any]:
    db = load_db()
    tx_id = f"tx_{int(datetime.now().timestamp() * 1000)}"
    new_tx = {
        "id": tx_id,
        "type": tx_type,
        "amount": amount,
        "category": category,
        "description": description,
        "date": datetime.now().isoformat(timespec="seconds"),
        "created_by": created_by
    }
    db.setdefault("transactions", []).insert(0, new_tx)
    save_db(db)
    return new_tx


def delete_transaction(tx_id: str) -> bool:
    db = load_db()
    txs = db.get("transactions", [])
    initial_len = len(txs)
    db["transactions"] = [tx for tx in txs if tx.get("id") != tx_id]
    if len(db["transactions"]) < initial_len:
        save_db(db)
        return True
    return False


def get_tasks() -> List[Dict[str, Any]]:
    db = load_db()
    return db.get("tasks", [])


def add_task(title: str, deadline: Optional[str] = None, priority: str = "medium") -> Dict[str, Any]:
    db = load_db()
    task_id = f"task_{int(datetime.now().timestamp() * 1000)}"
    new_task = {
        "id": task_id,
        "title": title,
        "deadline": deadline,
        "priority": priority,
        "status": "pending",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "completed_at": None
    }
    db.setdefault("tasks", []).insert(0, new_task)
    save_db(db)
    return new_task


def toggle_task(task_id: str) -> Optional[Dict[str, Any]]:
    db = load_db()
    tasks = db.get("tasks", [])
    target = None
    for t in tasks:
        if t.get("id") == task_id or t.get("title", "").lower() == task_id.lower():
            if t.get("status") == "completed":
                t["status"] = "pending"
                t["completed_at"] = None
            else:
                t["status"] = "completed"
                t["completed_at"] = datetime.now().isoformat(timespec="seconds")
            target = t
            break
    if target:
        save_db(db)
    return target


def complete_task_by_title(title_keyword: str) -> Optional[Dict[str, Any]]:
    db = load_db()
    tasks = db.get("tasks", [])
    keyword = title_keyword.lower().strip()
    target = None
    for t in tasks:
        if keyword in t.get("title", "").lower():
            t["status"] = "completed"
            t["completed_at"] = datetime.now().isoformat(timespec="seconds")
            target = t
            break
    if target:
        save_db(db)
    return target


def get_finance_summary() -> Dict[str, Any]:
    db = load_db()
    txs = db.get("transactions", [])
    total_income = sum(tx["amount"] for tx in txs if tx.get("type") == "income")
    total_expense = sum(tx["amount"] for tx in txs if tx.get("type") == "expense")
    balance = total_income - total_expense
    
    categories: Dict[str, float] = {}
    for tx in txs:
        if tx.get("type") == "expense":
            cat = tx.get("category", "Khác")
            categories[cat] = categories.get(cat, 0) + tx.get("amount", 0)
            
    budgets = db.get("budgets", {})
    monthly_limit = budgets.get("monthly_limit", 8000000)
    percent_budget = (total_expense / monthly_limit * 100) if monthly_limit > 0 else 0
    
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,
        "categories": categories,
        "monthly_limit": monthly_limit,
        "percent_budget": round(percent_budget, 1),
        "transaction_count": len(txs)
    }


def add_activity_log(input_text: str, routed_to: str, intent: str, confidence: float, latency_ms: float, status: str = "success") -> Dict[str, Any]:
    db = load_db()
    log_entry = {
        "id": f"log_{int(datetime.now().timestamp() * 1000)}",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "input": input_text,
        "routed_to": routed_to,
        "intent": intent,
        "confidence": round(confidence, 4),
        "latency_ms": round(latency_ms, 2),
        "status": status
    }
    db.setdefault("activity_logs", []).insert(0, log_entry)
    if len(db["activity_logs"]) > 50:
        db["activity_logs"] = db["activity_logs"][:50]
    save_db(db)
    return log_entry


def delete_task(task_id_or_title: str) -> bool:
    db = load_db()
    tasks = db.get("tasks", [])
    initial_len = len(tasks)
    kw = task_id_or_title.lower().strip()
    db["tasks"] = [t for t in tasks if t.get("id") != task_id_or_title and kw not in t.get("title", "").lower()]
    if len(db["tasks"]) < initial_len:
        save_db(db)
        return True
    return False


def update_task_priority(task_id_or_title: str, priority: str) -> Optional[Dict[str, Any]]:
    db = load_db()
    tasks = db.get("tasks", [])
    kw = task_id_or_title.lower().strip()
    target = None
    for t in tasks:
        if t.get("id") == task_id_or_title or kw in t.get("title", "").lower():
            t["priority"] = priority.lower()
            target = t
            break
    if target:
        save_db(db)
    return target


def set_monthly_budget(new_limit: float) -> Dict[str, Any]:
    db = load_db()
    db.setdefault("budgets", {})["monthly_limit"] = new_limit
    save_db(db)
    return db["budgets"]


def get_savings_goals() -> List[Dict[str, Any]]:
    db = load_db()
    return db.get("savings_goals", [])


def add_savings_goal(name: str, target_amount: float, deadline: Optional[str] = None) -> Dict[str, Any]:
    db = load_db()
    goal_id = f"goal_{int(datetime.now().timestamp() * 1000)}"
    new_goal = {
        "id": goal_id,
        "name": name,
        "target_amount": target_amount,
        "current_amount": 0,
        "deadline": deadline,
        "created_at": datetime.now().isoformat(timespec="seconds")
    }
    db.setdefault("savings_goals", []).append(new_goal)
    save_db(db)
    return new_goal


def deposit_savings_goal(goal_id_or_name: str, amount: float) -> Optional[Dict[str, Any]]:
    db = load_db()
    goals = db.get("savings_goals", [])
    kw = goal_id_or_name.lower().strip()
    target = None
    for g in goals:
        if g.get("id") == goal_id_or_name or kw in g.get("name", "").lower():
            g["current_amount"] = g.get("current_amount", 0) + amount
            target = g
            break
    if target:
        save_db(db)
    return target


def delete_savings_goal(goal_id: str) -> bool:
    db = load_db()
    goals = db.get("savings_goals", [])
    initial_len = len(goals)
    db["savings_goals"] = [g for g in goals if g.get("id") != goal_id]
    if len(db["savings_goals"]) < initial_len:
        save_db(db)
        return True
    return False


def get_reminders() -> List[Dict[str, Any]]:
    db = load_db()
    return db.get("reminders", [])


def add_reminder(text: str, remind_at: Optional[str] = None) -> Dict[str, Any]:
    db = load_db()
    rem_id = f"rem_{int(datetime.now().timestamp() * 1000)}"
    new_rem = {
        "id": rem_id,
        "text": text,
        "remind_at": remind_at,
        "status": "pending",
        "created_at": datetime.now().isoformat(timespec="seconds")
    }
    db.setdefault("reminders", []).insert(0, new_rem)
    save_db(db)
    return new_rem


def delete_reminder(rem_id: str) -> bool:
    db = load_db()
    rems = db.get("reminders", [])
    initial_len = len(rems)
    db["reminders"] = [r for r in rems if r.get("id") != rem_id]
    if len(db["reminders"]) < initial_len:
        save_db(db)
        return True
    return False


def get_notes() -> List[Dict[str, Any]]:
    db = load_db()
    return db.get("notes", [])


def add_note(content: str, category: str = "general") -> Dict[str, Any]:
    db = load_db()
    note_id = f"note_{int(datetime.now().timestamp() * 1000)}"
    new_note = {
        "id": note_id,
        "content": content,
        "category": category,
        "created_at": datetime.now().isoformat(timespec="seconds")
    }
    db.setdefault("notes", []).insert(0, new_note)
    save_db(db)
    return new_note


def filter_transactions(min_amount: Optional[float] = None, max_amount: Optional[float] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
    db = load_db()
    txs = db.get("transactions", [])
    res = txs
    if min_amount is not None:
        res = [t for t in res if t.get("amount", 0) >= min_amount]
    if max_amount is not None:
        res = [t for t in res if t.get("amount", 0) <= max_amount]
    if category:
        cat_lower = category.lower().strip()
        res = [t for t in res if cat_lower in t.get("category", "").lower()]
    return res


def reset_to_default():
    save_db(DEFAULT_DB.copy())
