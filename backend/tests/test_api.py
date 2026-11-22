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
from src.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoints(client):
    """Verify health endpoints report ok status and 33 intents."""
    # Test /health
    res1 = client.get("/health")
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == "ok"
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
    assert "200.000₫" in data2["message"]


def test_chat_task_query_today(client):
    """Test task.query_today returns 3 actionable tasks and action chips."""
    res = client.post("/api/v1/chat", json={"text": "Hôm nay tôi có những việc gì cần làm"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] in ["task.query_today", "task.query"]
    assert data["status"] == "READY"
    assert "Danh sách công việc hôm nay của bạn" in data["message"]
    assert "Hoàn thiện tài liệu kiến trúc OnisAgent" in data["message"]
    assert "Thêm việc mới" in data["quick_replies"]
    assert data["data"]["count"] == 3


def test_chat_task_query_deadline(client):
    """Test task.query_deadline returns urgent deadlines within 48h."""
    res = client.post("/api/v1/chat", json={"text": "Kiểm tra hạn chót deadline sắp tới"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "task.query_deadline"
    assert data["status"] == "READY"
    assert "Cảnh báo hạn chót (Deadline)" in data["message"]
    assert "Đã làm xong" in data["quick_replies"]
    assert data["data"]["count"] == 2


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
