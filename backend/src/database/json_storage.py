"""Small durable JSON repository for local/offline development.

The repository keeps the API useful without AWS credentials. It deliberately
uses strings for persisted money values and converts to Decimal at the edge.
The same repository contract can later be backed by DynamoDB.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4


class JsonStorage:
    """Durable local store for the finance/task domains."""

    _lock = RLock()
    _empty = {"transactions": [], "tasks": [], "debts": [], "budgets": [], "savings_goals": [], "reminders": [], "plans": []}

    def __init__(self, path: str | Path | None = None) -> None:
        default = Path(__file__).resolve().parents[2] / "data" / "local" / "onis_state.json"
        self.path = Path(path or os.getenv("LOCAL_STORAGE_PATH", default))

    def _read(self) -> dict[str, list[dict[str, Any]]]:
        with self._lock:
            if not self.path.exists():
                return {key: [] for key in self._empty}
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return {key: [] for key in self._empty}
            return {key: list(data.get(key, [])) for key in self._empty}

    def _write(self, data: dict[str, list[dict[str, Any]]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            fd, temp_name = tempfile.mkstemp(prefix="onis_state_", suffix=".json", dir=self.path.parent)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    json.dump(data, handle, ensure_ascii=False, indent=2, default=str)
                    handle.write("\n")
                os.replace(temp_name, self.path)
            finally:
                if os.path.exists(temp_name):
                    os.unlink(temp_name)

    @staticmethod
    def _money(value: Any) -> str:
        return str(Decimal(str(value)))

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    def add_transaction(self, user_id: str, *, amount: Any, transaction_type: str, description: str, category: str = "Khác", account: str = "default_account") -> dict[str, Any]:
        item = {
            "id": f"tx_{uuid4().hex[:12]}", "user_id": user_id,
            "amount": self._money(amount), "type": transaction_type,
            "description": description, "category": category,
            "account": account, "created_at": self._now(),
        }
        data = self._read(); data["transactions"].append(item); self._write(data); return item

    def list_transactions(self, user_id: str, *, category: str | None = None, keyword: str | None = None) -> list[dict[str, Any]]:
        rows = [x for x in self._read()["transactions"] if x.get("user_id") == user_id]
        if category and category.lower() not in {"all", "tất cả"}:
            rows = [x for x in rows if category.casefold() in str(x.get("category", "")).casefold()]
        if keyword and keyword not in {"all", "tất cả"}:
            rows = [x for x in rows if keyword.casefold() in json.dumps(x, ensure_ascii=False).casefold()]
        return rows

    def summary(self, user_id: str) -> dict[str, Decimal]:
        income = sum((Decimal(x["amount"]) for x in self.list_transactions(user_id) if x.get("type") == "income"), Decimal("0"))
        expense = sum((Decimal(x["amount"]) for x in self.list_transactions(user_id) if x.get("type") == "expense"), Decimal("0"))
        return {"income": income, "expense": expense, "balance": income - expense}

    def add_task(self, user_id: str, slots: dict[str, Any]) -> dict[str, Any]:
        item = {"id": f"task_{uuid4().hex[:12]}", "user_id": user_id, "status": "pending", "created_at": self._now(), **slots}
        data = self._read(); data["tasks"].append(item); self._write(data); return item

    def list_tasks(self, user_id: str, *, status: str | None = "pending", keyword: str | None = None) -> list[dict[str, Any]]:
        rows = [x for x in self._read()["tasks"] if x.get("user_id") == user_id]
        if status and status != "all": rows = [x for x in rows if x.get("status") == status]
        if keyword: rows = [x for x in rows if keyword.casefold() in json.dumps(x, ensure_ascii=False).casefold()]
        return rows

    def update_task(self, user_id: str, slots: dict[str, Any], status: str) -> dict[str, Any] | None:
        data = self._read(); found = None
        for item in data["tasks"]:
            if item.get("user_id") != user_id: continue
            if slots.get("task_id") and item.get("id") == slots["task_id"] or slots.get("title") and slots["title"].casefold() in item.get("title", "").casefold():
                item["status"] = status; item["updated_at"] = self._now(); found = item; break
        if found: self._write(data)
        return found

    def delete_task(self, user_id: str, slots: dict[str, Any]) -> dict[str, Any] | None:
        data = self._read(); found = None
        kept = []
        for item in data["tasks"]:
            match = item.get("user_id") == user_id and ((slots.get("task_id") and item.get("id") == slots["task_id"]) or (slots.get("title") and slots["title"].casefold() in item.get("title", "").casefold()))
            if match and found is None: found = item
            else: kept.append(item)
        if found: data["tasks"] = kept; self._write(data)
        return found

    def add_record(self, collection: str, user_id: str, values: dict[str, Any]) -> dict[str, Any]:
        item = {"id": f"{collection}_{uuid4().hex[:12]}", "user_id": user_id, "created_at": self._now(), **values}
        data = self._read(); data[collection].append(item); self._write(data); return item

    def list_records(self, collection: str, user_id: str) -> list[dict[str, Any]]:
        return [x for x in self._read()[collection] if x.get("user_id") == user_id]
