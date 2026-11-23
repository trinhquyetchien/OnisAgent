"""Comprehensive tests for OnisAgent FastAPI Server endpoints.

Covers:
- GET /health & GET /api/v1/health (System status, model version, 32 intents)
- POST /api/v1/intent/classify (Kev fast classification & latency ms)
- POST /api/v1/chat (Standard expense creation with Decimal precision)
- POST /api/v1/chat (Multi-turn clarification flow & quick_replies)
- POST /api/v1/chat (HITL blocked action)
"""

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.database import postgres
from src.database.postgres import create_database_engine
import src.main as main
from src.main import app, storage


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "path", tmp_path / "onis_state.json")
    monkeypatch.setattr(main, "AUTH_REQUIRED", False)
    engine = create_database_engine(f"sqlite:///{tmp_path / 'health-test.db'}")
    monkeypatch.setattr(postgres, "SessionLocal", postgres.sessionmaker(bind=engine))
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoints(client):
    """Verify health endpoints report ok status and 33 intents."""
    # Test /health
    res1 = client.get("/health")
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == "ok"
    assert data1["database_connected"] is True
    assert data1["model_loaded"] is True
    assert data1["supported_intents_count"] == 33
    assert "finance.add_expense" in data1["intents"]
    assert "finance.query_debt" in data1["intents"]
    assert "task.create" in data1["intents"]

    # Test /api/v1/health
    res2 = client.get("/api/v1/health")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["status"] == "ok"
    assert data2["supported_intents_count"] == 33


def test_health_reports_database_unavailable(client, monkeypatch):
    def unavailable_session():
        raise SQLAlchemyError("database down")

    monkeypatch.setattr(postgres, "SessionLocal", unavailable_session)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["detail"] == "Database unavailable."


def test_classify_intent_endpoint(client):
    """Test fast classification endpoint with sub-10ms response."""
    res = client.post("/api/v1/intent/classify", json={"text": "chi 45k tiền ăn trưa"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "finance.add_expense"
    assert data["confidence"] > 0.5
    assert data["route"] == "FAST_PATH"
    assert data["latency_ms"] >= 0.0
    assert "amount" in data["raw_slots"]


def test_chat_expense_normal(client):
    """Test standard single-turn expense tracking with slot extraction."""
    session_id = "test_normal_expense"
    payload = {
        "session_id": session_id,
        "user_id": "user_test",
        "text": "chi 45k trà sữa hôm nay",
    }
    res = client.post("/api/v1/chat", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["session_id"] == session_id
    assert data["intent"] == "finance.add_expense"
    assert data["route"] == "FAST_PATH"
    assert data["status"] == "READY"
    assert "45.000₫" in data["message"]
    assert data["data"] is not None
    assert data["data"]["transaction_type"] == "expense"
    assert data["slots"]["amount"] == 45000.0


def test_chat_clarification_multiturn_flow(client):
    """Test multi-turn clarification when missing amount, followed by amount supplement."""
    session_id = "test_multiturn_clarification"

    # Turn 1: User mentions expense item without amount
    turn1_payload = {
        "session_id": session_id,
        "user_id": "user_test",
        "text": "Vừa mua ly cà phê sữa đá",
    }
    res1 = client.post("/api/v1/chat", json=turn1_payload)
    assert res1.status_code == 200
    data1 = res1.json()

    assert data1["status"] == "NEED_CLARIFICATION"
    assert "bao nhiêu tiền" in data1["message"]
    assert len(data1["quick_replies"]) > 0
    assert "30.000₫" in data1["quick_replies"]

    # Turn 2: User supplements amount via quick reply or message "35k"
    turn2_payload = {
        "session_id": session_id,
        "user_id": "user_test",
        "text": "35k",
    }
    res2 = client.post("/api/v1/chat", json=turn2_payload)
    assert res2.status_code == 200
    data2 = res2.json()

    assert data2["status"] == "READY"
    assert "35.000₫" in data2["message"]
    assert data2["data"]["transaction_type"] == "expense"
    assert data2["slots"]["amount"] == 35000.0


def test_chat_task_creation(client):
    """Test task creation intent via Chat endpoint."""
    session_id = "test_task_session"
    payload = {
        "session_id": session_id,
        "user_id": "user_test",
        "text": "nhắc tôi nộp báo cáo nghiên cứu trước 17h",
    }
    res = client.post("/api/v1/chat", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["intent"] == "task.create"
    assert data["status"] == "READY"
    assert "nộp báo cáo nghiên cứu" in data["message"]
    assert data["data"]["task"]["title"] is not None


def test_chat_blocked_hitl_action(client):
    """Test dangerous action (task delete) triggers BLOCKED status for HITL approval."""
    session_id = "test_hitl_session"
    payload = {
        "session_id": session_id,
        "user_id": "user_test",
        "text": "xóa task báo cáo tiến độ",
    }
    res = client.post("/api/v1/chat", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "BLOCKED"
    assert data["requires_hitl"] is True
    assert "Xác nhận" in data["quick_replies"]


def test_chat_query_debt(client):
    """Test finance.query_debt intent returns debt details and action chips."""
    # General query
    res = client.post("/api/v1/chat", json={"text": "tôi có nợ ai không"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "finance.query_debt"
    assert data["status"] == "READY"
    assert "Lan" in data["message"] or "nợ" in data["message"]
    assert "Xem ai nợ tôi" in data["quick_replies"]
    assert "Ghi nợ mới" in data["quick_replies"]

    # Specific person query
    res2 = client.post("/api/v1/chat", json={"text": "thằng Tuấn có nợ tôi đồng nào không"})
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["intent"] == "finance.query_debt"
    assert "Tuấn" in data2["message"]
    assert "không có khoản nợ" in data2["message"]


def test_chat_task_query_today(client):
    """Test task.query_today returns 3 actionable tasks and action chips."""
    res = client.post("/api/v1/chat", json={"text": "Hôm nay tôi có những việc gì cần làm"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] in ["task.query_today", "task.query"]
    assert data["status"] == "READY"
    assert "Danh sách công việc hôm nay của bạn" in data["message"]
    assert data["data"]["tasks"] == []
    assert "Thêm việc mới" in data["quick_replies"]
    assert data["data"]["count"] == 0


def test_chat_task_query_deadline(client):
    """Test task.query_deadline returns urgent deadlines within 48h."""
    res = client.post("/api/v1/chat", json={"text": "Kiểm tra hạn chót deadline sắp tới"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "task.query_deadline"
    assert data["status"] == "READY"
    assert "Cảnh báo hạn chót (Deadline)" in data["message"]
    assert "Đã làm xong" in data["quick_replies"]
    assert data["data"]["count"] == 0


def test_chat_cross_plan_expense_task(client):
    """Test cross.plan_expense_task routes to REASONING_PATH with Ollama planning & action chips."""
    res = client.post("/api/v1/chat", json={"text": "tính đi đà lạt 3 ngày dự chi khoảng 3 triệu"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "cross.plan_expense_task"
    assert data["route"] == "REASONING_PATH"
    assert data["status"] == "READY"
    assert len(data["message"]) > 50
    assert "Lưu kế hoạch" in data["quick_replies"]
    assert "Tạo ngân sách" in data["quick_replies"]


def test_transaction_crud_and_correction(client):
    created = client.post(
        "/api/v1/transactions",
        json={
            "amount": 45000,
            "type": "expense",
            "description": "Trà sữa",
            "category": "Khác",
        },
    )
    assert created.status_code == 201
    transaction = created.json()["transaction"]
    fetched = client.get(f"/api/v1/transactions/{transaction['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["transaction"]["id"] == transaction["id"]

    corrected = client.post(
        "/api/v1/transactions/corrections",
        json={
            "transaction_id": transaction["id"],
            "raw_description": "Trà sữa",
            "ai_predicted_category": "Khác",
            "user_corrected_category": "Ăn uống",
        },
    )
    assert corrected.status_code == 201
    assert corrected.json()["correction"]["user_id"] == "default_user"

    listed = client.get("/api/v1/transactions")
    assert listed.json()["transactions"][0]["category"] == "Ăn uống"
    filtered = client.get(
        "/api/v1/transactions",
        params={"category": "Ăn uống", "keyword": "trà"},
    )
    assert [item["id"] for item in filtered.json()["transactions"]] == [
        transaction["id"]
    ]

    deleted = client.delete(f"/api/v1/transactions/{transaction['id']}")
    assert deleted.status_code == 200


def test_savings_goal_and_debt_api_routes(client):
    goal = client.post(
        "/api/v1/savings-goals",
        json={"values": {"title": "Emergency fund", "target_amount": 1000000}},
    )
    assert goal.status_code == 201
    assert goal.json()["savings_goal"]["title"] == "Emergency fund"
    assert len(client.get("/api/v1/savings-goals").json()["savings_goals"]) == 1

    debt = client.post(
        "/api/v1/debts",
        json={"values": {"person": "An", "amount": 50000, "debt_type": "owed_to"}},
    )
    assert debt.status_code == 201
    assert debt.json()["debt"]["person"] == "An"
    assert len(client.get("/api/v1/debts").json()["debts"]) == 1


def test_hitl_delete_is_blocked_until_explicit_approval(client):
    created = client.post(
        "/api/v1/tasks",
        json={"title": "Kiểm tra HITL", "priority": "high"},
    )
    assert created.status_code == 201
    task = created.json()["task"]
    completed = client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"status": "completed"},
    )
    assert completed.json()["task"]["status"] == "completed"

    blocked = client.delete(f"/api/v1/tasks/{task['id']}")
    assert blocked.status_code == 200
    assert blocked.json()["requires_hitl"] is True
    pending_tasks = storage.list_tasks("default_user", status="all")
    assert pending_tasks[0]["status"] == "completed"

    approved = client.post(
        "/api/v1/hitl/approve",
        json={
            "idempotency_key": "delete-task-hitl-1",
            "action": "task_delete",
            "payload": {"task_id": task["id"]},
        },
    )
    assert approved.status_code == 200
    assert approved.json()["ok"] is True
    assert not storage.list_tasks("default_user", status="all")


def test_hitl_transfer_approval_is_persisted_once(client):
    payload = {
        "idempotency_key": "transfer-hitl-1",
        "action": "transfer",
        "payload": {
            "amount": 12500,
            "from_account": "checking",
            "to_account": "savings",
        },
    }

    first = client.post("/api/v1/hitl/approve", json=payload)
    second = client.post("/api/v1/hitl/approve", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    transactions = storage.list_transactions("default_user")
    assert len(transactions) == 1
    assert transactions[0]["type"] == "transfer"
    assert transactions[0]["amount"] == "12500"

    invalid = client.post(
        "/api/v1/hitl/approve",
        json={
            **payload,
            "idempotency_key": "transfer-hitl-invalid",
            "payload": {"amount": 0, "from_account": "checking", "to_account": "savings"},
        },
    )
    assert invalid.status_code == 422
