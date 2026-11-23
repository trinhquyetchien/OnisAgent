"""FastAPI Server for OnisAgent Backend.

Provides production-ready RESTful endpoints connecting:
- Kev Decision Model (Fast Path sub-10ms classification)
- Slot Validator & Multi-turn Session Manager (Clarification Engine)
- Decimal Tools (100% precision financial calculator)
- Full API for Flutter Web and Mobile clients
"""

from contextlib import asynccontextmanager
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import time
import unicodedata
import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import joblib
import numpy as np
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from src.agents.ollama_client import ollama_client
from src.engine.response_templates import (
    format_currency,
    template_finance_split_bill,
    template_system_help,
    template_task_create,
    template_task_complete,
)
from src.engine.session_manager import SessionManager
from src.engine.slot_validator import SlotValidator
from src.database.json_storage import JsonStorage
from src.auth_service import AuthError
from src.schemas.base import ExecutionStatus
from src.tools.calculator import calculate_loan_amortization
from src.database import postgres
from src.models import auth_models  # noqa: F401 - register SQLAlchemy auth tables
from src.api_auth import router as auth_router
from src.models.auth_models import AuthUser
from src.security import verify_access_token
import jwt

# ----------------- CONSTANTS & PATHS -----------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "checkpoints" / "kev" / "kev_intent_model.joblib"
CONFIDENCE_THRESHOLD = 0.50  # Validate/recalibrate this threshold on a held-out set.


def _looks_like_task_today_query(text: str) -> bool:
    """Guard common ASR/typo variants before intent classification."""
    folded = unicodedata.normalize("NFD", text.lower())
    folded = "".join(char for char in folded if unicodedata.category(char) != "Mn")
    folded = re.sub(r"đ", "d", folded)
    folded = re.sub(r"\s+", " ", folded).strip()
    if "lap ke hoach" in folded or "len ke hoach" in folded or "sap xep" in folded or "toi uu hoa thoi gian" in folded:
        return False
    has_task_noun = any(term in folded for term in ("viec", "cong viec", "task", "lich"))
    has_query_marker = any(
        marker in folded
        for marker in ("hom nay", "nay", "co viec", "co task", "liet ke", "xem viec")
    )
    has_create_marker = any(
        marker in folded
        for marker in ("tao", "them", "nhac toi", "ghi chu", "dat lich", "len lich")
    )
    return has_task_noun and has_query_marker and not has_create_marker


def _looks_like_task_plan(text: str) -> bool:
    folded = unicodedata.normalize("NFD", text.lower())
    folded = "".join(char for char in folded if unicodedata.category(char) != "Mn")
    folded = re.sub(r"đ", "d", folded)
    return any(term in folded for term in ("lap ke hoach", "len ke hoach", "sap xep thu tu", "toi uu hoa thoi gian", "ke hoach lam viec"))


def _looks_like_cross_plan(text: str) -> bool:
    folded = unicodedata.normalize("NFD", text.lower())
    folded = "".join(char for char in folded if unicodedata.category(char) != "Mn")
    folded = re.sub(r"đ", "d", folded)
    return _looks_like_task_plan(text) and any(
        term in folded for term in ("tiec", "du lich", "offline", "su kien", "to chuc")
    )


def _looks_like_budget_plan(text: str) -> bool:
    folded = unicodedata.normalize("NFD", text.lower())
    folded = "".join(char for char in folded if unicodedata.category(char) != "Mn")
    folded = re.sub(r"đ", "d", folded)
    return "ngan sach" in folded and not _looks_like_cross_plan(text)


def _looks_like_greeting_summary(text: str) -> bool:
    folded = unicodedata.normalize("NFD", text.lower())
    folded = "".join(char for char in folded if unicodedata.category(char) != "Mn")
    folded = re.sub(r"đ", "d", folded)
    has_greeting = any(term in folded for term in ("chao", "hello", "xin chao", "buoi sang"))
    has_summary = any(term in folded for term in ("tom tat", "diem tin", "tong quan", "tinh hinh"))
    return has_greeting and (has_summary or "bao nhieu tien" in folded or "bao nhieu task" in folded)


# ----------------- IN-MEMORY APPLICATION STATE -----------------
class AppState:
    kev_model: Any = None
    session_manager: SessionManager = SessionManager()
    supported_intents: list[str] = []


state = AppState()
storage = JsonStorage()
# Production API calls must be associated with a real authenticated account.
# Tests that exercise unauthenticated legacy endpoints explicitly override this
# module flag in their isolated fixture.
AUTH_REQUIRED = os.getenv("AUTH_REQUIRED", "true").casefold() == "true"


def load_kev_model() -> Any:
    """Load trained Kev Intent Classification pipeline."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Kev model checkpoint not found at {MODEL_PATH}. "
            "Please train the model first with scripts/training/train_kev_local.py."
        )
    return joblib.load(MODEL_PATH)


def get_kev_model() -> Any:
    """Return loaded model or lazy-load if not initialized."""
    if state.kev_model is None:
        try:
            state.kev_model = load_kev_model()
            state.supported_intents = sorted(list(state.kev_model.classes_))
        except Exception:
            state.kev_model = None
            state.supported_intents = []
    return state.kev_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    try:
        postgres.init_db()
        print("🗄️ [Database] Authentication schema is ready.")
    except Exception as exc:
        # Keep health endpoints available so an operator can see the database
        # failure instead of masking it with an import/startup error.
        print(f"⚠️ [Database Warning] Could not initialize authentication schema: {exc}")
    try:
        state.kev_model = load_kev_model()
        state.supported_intents = sorted(list(state.kev_model.classes_))
        print(f"🚀 [Kev Fast Path] Model loaded: {len(state.supported_intents)} intents ready.")
    except Exception as exc:
        print(f"⚠️ [Startup Warning] Could not load Kev checkpoint: {exc}")
        state.kev_model = None
        state.supported_intents = []
    yield
    print("🛑 OnisAgent FastAPI server shutting down.")


# ----------------- FASTAPI APP SETUP -----------------
app = FastAPI(
    title="OnisAgent Backend Core API",
    version="1.0.0",
    description="Cognitive Multi-turn API with Kev Fast Path & Ollama Reasoning",
    lifespan=lifespan,
)

# Enable CORS for Flutter Web / Mobile clients / Localhost
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
    "http://localhost:5000",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:5000",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


# ----------------- SCHEMAS -----------------
def parse_slots_from_text(text: str, intent: str) -> dict[str, Any]:
    """Helper heuristic slot extractor for common Vietnamese utterances."""
    slots: dict[str, Any] = {}
    lower = text.lower()

    # 1. Amount extraction (e.g., 45k, 45.000, 2 củ, 5 lít, 2 xị, 1tr, 500 ngàn)
    match_k = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:k|nghìn|ngàn|d|đ|vnd)", lower)
    match_cu = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:củ|triệu|tr)", lower)
    match_xi = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:xị)", lower)
    match_lit = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:lít)", lower)
    match_num = re.search(r"\b(\d{4,})\b", lower)

    if match_k:
        slots["amount"] = Decimal(match_k.group(1).replace(",", ".")) * 1000
    elif match_cu:
        slots["amount"] = Decimal(match_cu.group(1).replace(",", ".")) * 1_000_000
    elif match_xi:
        slots["amount"] = Decimal(match_xi.group(1).replace(",", ".")) * 100_000
    elif match_lit:
        slots["amount"] = Decimal(match_lit.group(1).replace(",", ".")) * 100_000
    elif match_num:
        slots["amount"] = Decimal(match_num.group(1))

    if slots.get("amount") is not None:
        if "loan_installment_plan" in intent or "loan.calculate" in intent:
            slots["principal"] = slots["amount"]
        elif "savings_goal" in intent or "savings.create" in intent:
            slots["target_amount"] = slots["amount"]
        elif "budget_plan" in intent or "update_budget" in intent:
            slots["limit_amount"] = slots["amount"]

    term_match = re.search(r"\b(\d+)\s*(?:tháng|thang|thg)\b", lower)
    if term_match and ("loan" in intent or "installment" in intent):
        slots["term_months"] = int(term_match.group(1))
    rate_match = re.search(r"(?:lãi|lai|rate)\s*(\d+(?:[.,]\d+)?)\s*%?", lower)
    if rate_match and ("loan" in intent or "installment" in intent):
        slots["annual_rate"] = Decimal(rate_match.group(1).replace(",", "."))

    # 2. Finance Category / Note heuristics
    if any(w in lower for w in ["trà sữa", "cà phê", "cafe", "ăn trưa", "ăn sáng", "ăn tối", "cơm", "phở", "bún", "bánh mì"]):
        slots["category"] = "Ăn uống"
        slots["note"] = text
    elif any(w in lower for w in ["xăng", "grab", "be", "taxi", "gửi xe", "xe bus"]):
        slots["category"] = "Di chuyển"
        slots["note"] = text
    elif any(w in lower for w in ["tiền điện", "tiền nước", "tiền mạng", "internet", "tiền nhà", "tiền trọ"]):
        slots["category"] = "Hóa đơn"
        slots["note"] = text
    elif any(w in lower for w in ["shopee", "tiki", "lazada", "mua sắm", "quần áo"]):
        slots["category"] = "Mua sắm"
        slots["note"] = text

    if "add_expense" in intent and slots.get("amount") is not None and not slots.get("category") and not slots.get("note"):
        slots["note"] = text

    # 3. Source heuristic for income
    if "income" in intent:
        if "lương" in lower:
            slots["source"] = "Lương"
        elif "thưởng" in lower:
            slots["source"] = "Tiền thưởng"
        elif "bán hàng" in lower:
            slots["source"] = "Bán hàng"
        elif "mẹ cho" in lower or "bố cho" in lower or "ba cho" in lower:
            slots["source"] = "Gia đình chu cấp"

    # 4. Debt Query heuristic
    if "query_debt" in intent:
        if any(w in lower for w in ["ai nợ", "ai vay", "ai mượn", "ai thiếu", "người ta nợ", "con nợ", "cho vay", "cho mượn"]):
            slots["debt_type"] = "lend"
        elif any(w in lower for w in ["tôi nợ", "tôi vay", "tôi mượn", "tôi thiếu", "mình nợ", "tao nợ"]):
            slots["debt_type"] = "borrow"
        else:
            slots["debt_type"] = "all"

        for name in ["tuấn", "hải", "lan", "nam", "huy", "hùng", "thảo", "hoàng", "hương", "minh", "linh", "mẹ"]:
            if name in lower:
                slots["person"] = name.capitalize()
                break

    if any(key in intent for key in ("record_debt", "debt_repay")):
        slots.setdefault("debt_type", "lend" if "record_debt" in intent else "borrow")
        for name in ["tuấn", "hải", "lan", "nam", "huy", "hùng", "hằng", "phương", "thảo", "hoàng", "hương", "minh", "linh", "mẹ", "bố"]:
            if name in lower:
                slots.setdefault("person", name.capitalize())
                break

    if "transfer" in intent:
        account_match = re.search(r"(?:từ|tu)\s+(.+?)\s+(?:sang|qua|vào|vao)\s+(.+?)(?:\s+(?:giúp|giup|nhé|nhe|đi|di)\b|$)", lower)
        if not account_match:
            account_match = re.search(r"(?:vào|vao)\s+(.+?)\s+(?:từ|tu)\s+(.+?)(?:\s+(?:giúp|giup|nhé|nhe|đi|di)\b|$)", lower)
        if account_match:
            if "vào" in account_match.group(0) or "vao" in account_match.group(0):
                slots["to_account"] = account_match.group(1).strip()
                slots["from_account"] = account_match.group(2).strip()
            else:
                slots["from_account"] = account_match.group(1).strip()
                slots["to_account"] = account_match.group(2).strip()

    if "split_bill" in intent:
        people_match = re.search(r"(?:cho|với|voi)\s+(\d+)\s*(?:người|nguoi|đứa|dua)", lower)
        if people_match:
            slots["participants"] = int(people_match.group(1))

    if "query_transactions" in intent:
        known_category = next((value for value in ("ăn uống", "đi lại", "di chuyển", "mua sắm", "hóa đơn", "giáo dục") if value in lower), None)
        if known_category:
            slots["category"] = known_category
        slots.setdefault("time_range", "today" if "hôm nay" in lower or "hom nay" in lower else "all")
    elif any(key in intent for key in ("query_by_tag", "search")):
        slots.setdefault("keyword", text)

    if "budget" in intent:
        slots.setdefault("category", "all")
    if "bill_due_reminder" in intent:
        slots.setdefault("bill_name", text)
        slots.setdefault("due_date", "ngày mai" if "mai" in lower else "chưa xác định")

    # 5. Task title extraction
    if intent.startswith("task."):
        title = re.sub(
            r"^(tạo task|tạo việc|nhắc tôi|lên lịch|cần làm|thêm việc|hoàn thành|xóa task|hủy|huỷ|dời|lùi|tìm|tìm kiếm)\s*",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()
        if title:
            slots["title"] = title

    if intent == "task.schedule_event":
        slots.setdefault("start_time", text)
    if intent in {"task.reschedule", "task.cancel"}:
        slots.setdefault("new_deadline", text if "reschedule" in intent else None)
    if intent == "task.create_recurring":
        slots.setdefault("recurrence", "theo lịch người dùng nói")
    if intent == "task.plan_schedule":
        slots.setdefault("time_frame", "hôm nay" if "hôm nay" in lower or "hom nay" in lower else "tuần này")
    if intent == "finance.savings_goal":
        slots.setdefault("goal_name", text)

    return slots


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    database_connected: bool
    model_loaded: bool
    supported_intents_count: int
    intents: list[str]


class ClassifyRequest(BaseModel):
    text: str = Field(..., min_length=1, description="User utterance to classify")


class ClassifyResponse(BaseModel):
    intent: str
    confidence: float
    route: str  # "FAST_PATH" or "REASONING_PATH"
    latency_ms: float
    raw_slots: dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    session_id: str = Field(default="default_session", description="Unique conversation session ID")
    user_id: str = Field(default="default_user", description="Unique user identifier")
    text: str = Field(..., min_length=1, description="Message text from user")
    slots: dict[str, Any] | None = Field(default=None, description="Explicit slot overrides if any")
    user_confirmed: bool = Field(default=False, description="Explicit approval for sensitive actions")
    idempotency_key: str | None = Field(default=None, description="Stable key used to prevent duplicate HITL execution")


class AuthCredentials(BaseModel):
    email: str = Field(..., min_length=5, max_length=254)
    password: str = Field(..., min_length=8, max_length=256)


class RegisterRequest(AuthCredentials):
    name: str = Field(..., min_length=1, max_length=100)


class AuthResponse(BaseModel):
    user: dict[str, Any]
    access_token: str
    token_type: str = "Bearer"


class TransactionRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    type: str = Field(..., pattern="^(income|expense|transfer)$")
    description: str = Field(..., min_length=1, max_length=500)
    category: str = "Khác"
    account: str = "default_account"


class TransactionUpdateRequest(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0)
    type: str | None = Field(default=None, pattern="^(income|expense|transfer)$")
    description: str | None = Field(default=None, min_length=1, max_length=500)
    category: str | None = None
    account: str | None = None


class TaskRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    deadline: str | None = None
    priority: str = "medium"
    category: str = "Chung"
    is_important: bool = False


class RecordRequest(BaseModel):
    values: dict[str, Any] = Field(default_factory=dict)


class CorrectionRequest(BaseModel):
    transaction_id: str
    raw_description: str
    ai_predicted_category: str
    user_corrected_category: str


class HitlApprovalRequest(BaseModel):
    idempotency_key: str = Field(..., min_length=1, max_length=200)
    action: str = Field(..., pattern="^(task_delete|savings_create|loan_apply|transfer|balance_override|bulk_delete)$")
    payload: dict[str, Any] = Field(default_factory=dict)


def _resolve_user(authorization: str | None) -> dict[str, Any] | None:
    if not authorization:
        if AUTH_REQUIRED:
            raise HTTPException(status_code=401, detail="Cần đăng nhập để sử dụng API này.")
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.casefold() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Authorization phải có dạng Bearer token.")
    try:
        user_id = verify_access_token(
            token,
            os.getenv("AUTH_SECRET", ""),
            os.getenv("AUTH_JWT_ISSUER", "onisagent").strip(),
        )
        with postgres.SessionLocal() as db:
            user = db.scalar(select(AuthUser).where(AuthUser.id == user_id))
        if not user or not user.is_active:
            raise AuthError("Tài khoản không tồn tại.")
        return {
            "id": str(user.id),
            "email": user.email,
            "name": user.display_name,
        }
    except (jwt.PyJWTError, ValueError, AuthError) as exc:
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc đã hết hạn.") from exc



@app.get("/api/v1/transactions", tags=["Transactions"])
def list_transactions(
    category: str | None = None,
    keyword: str | None = None,
    authorization: str | None = Header(default=None),
):
    user = _resolve_user(authorization)
    if not user and AUTH_REQUIRED:
        raise HTTPException(status_code=401, detail="Cần đăng nhập.")
    user_id = user["id"] if user else "default_user"
    return {
        "transactions": storage.list_transactions(
            user_id,
            category=category,
            keyword=keyword,
        )
    }


@app.post("/api/v1/transactions", status_code=status.HTTP_201_CREATED, tags=["Transactions"])
def create_transaction(request: TransactionRequest, authorization: str | None = Header(default=None)):
    user = _resolve_user(authorization)
    if not user and AUTH_REQUIRED:
        raise HTTPException(status_code=401, detail="Cần đăng nhập.")
    user_id = user["id"] if user else "default_user"
    item = storage.add_transaction(
        user_id,
        amount=request.amount,
        transaction_type=request.type,
        description=request.description,
        category=request.category,
        account=request.account,
    )
    return {"transaction": item}


@app.get("/api/v1/transactions/{transaction_id}", tags=["Transactions"])
def get_transaction(transaction_id: str, authorization: str | None = Header(default=None)):
    user = _resolve_user(authorization)
    user_id = user["id"] if user else "default_user"
    item = storage.get_transaction(user_id, transaction_id)
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy giao dịch.")
    return {"transaction": item}


@app.patch("/api/v1/transactions/{transaction_id}", tags=["Transactions"])
def update_transaction(transaction_id: str, request: TransactionUpdateRequest, authorization: str | None = Header(default=None)):
    user = _resolve_user(authorization)
    user_id = user["id"] if user else "default_user"
    item = storage.update_transaction(user_id, transaction_id, request.model_dump(exclude_none=True))
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy giao dịch.")
    return {"transaction": item}


@app.delete("/api/v1/transactions/{transaction_id}", tags=["Transactions"])
def delete_transaction(transaction_id: str, authorization: str | None = Header(default=None)):
    user = _resolve_user(authorization)
    user_id = user["id"] if user else "default_user"
    item = storage.delete_transaction(user_id, transaction_id)
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy giao dịch.")
    return {"ok": True, "transaction": item}


@app.get("/api/v1/tasks", tags=["Tasks"])
def list_tasks(status_filter: str | None = None, authorization: str | None = Header(default=None)):
    user = _resolve_user(authorization)
    user_id = user["id"] if user else "default_user"
    return {"tasks": storage.list_tasks(user_id, status=status_filter or "all")}


@app.post("/api/v1/tasks", status_code=status.HTTP_201_CREATED, tags=["Tasks"])
def create_task(request: TaskRequest, authorization: str | None = Header(default=None)):
    user = _resolve_user(authorization)
    user_id = user["id"] if user else "default_user"
    item = storage.add_task(user_id, request.model_dump(exclude_none=True))
    return {"task": item}


@app.patch("/api/v1/tasks/{task_id}", tags=["Tasks"])
def update_task(task_id: str, request: dict[str, Any], authorization: str | None = Header(default=None)):
    user = _resolve_user(authorization)
    user_id = user["id"] if user else "default_user"
    new_status = str(request.get("status", "pending"))
    item = storage.update_task(user_id, {"task_id": task_id, **request}, new_status)
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc.")
    return {"task": item}


@app.delete("/api/v1/tasks/{task_id}", tags=["Tasks"])
def delete_task_api(task_id: str, authorization: str | None = Header(default=None)):
    user = _resolve_user(authorization)
    user_id = user["id"] if user else "default_user"
    item = next(
        (
            task for task in storage.list_tasks(user_id, status="all")
            if task.get("id") == task_id
        ),
        None,
    )
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc.")
    return {
        "ok": False,
        "status": "BLOCKED",
        "requires_hitl": True,
        "task": item,
        "message": "Cần xác nhận HITL trước khi xóa công việc.",
    }


@app.get("/api/v1/savings-goals", tags=["Savings"])
def list_savings_goals(authorization: str | None = Header(default=None)):
    user = _resolve_user(authorization)
    user_id = user["id"] if user else "default_user"
    return {"savings_goals": storage.list_records("savings_goals", user_id)}


@app.post("/api/v1/savings-goals", status_code=status.HTTP_201_CREATED, tags=["Savings"])
def create_savings_goal(request: RecordRequest, authorization: str | None = Header(default=None)):
    user = _resolve_user(authorization)
    user_id = user["id"] if user else "default_user"
    item = storage.add_record("savings_goals", user_id, request.values)
    return {"savings_goal": item}


@app.get("/api/v1/debts", tags=["Debts"])
def list_debts(authorization: str | None = Header(default=None)):
    user = _resolve_user(authorization)
    user_id = user["id"] if user else "default_user"
    return {"debts": storage.list_records("debts", user_id)}


@app.post("/api/v1/debts", status_code=status.HTTP_201_CREATED, tags=["Debts"])
def create_debt(request: RecordRequest, authorization: str | None = Header(default=None)):
    user = _resolve_user(authorization)
    user_id = user["id"] if user else "default_user"
    item = storage.add_record("debts", user_id, request.values)
    return {"debt": item}


@app.post("/api/v1/transactions/corrections", status_code=status.HTTP_201_CREATED, tags=["Corrections"])
def add_transaction_correction(request: CorrectionRequest, authorization: str | None = Header(default=None)):
    user = _resolve_user(authorization)
    user_id = user["id"] if user else "default_user"
    transaction = storage.get_transaction(user_id, request.transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Không tìm thấy giao dịch.")
    item = storage.add_correction(user_id, request.model_dump())
    storage.update_transaction(
        user_id,
        request.transaction_id,
        {"category": request.user_corrected_category},
    )
    return {"correction": item}


@app.post("/api/v1/hitl/approve", tags=["HITL"])
def approve_hitl(request: HitlApprovalRequest, authorization: str | None = Header(default=None)):
    user = _resolve_user(authorization)
    user_id = user["id"] if user else "default_user"
    action = {"action": request.action, "payload": request.payload}
    existing = next(
        (
            item for item in storage.list_records("hitl_approvals", user_id)
            if item.get("idempotency_key") == request.idempotency_key
        ),
        None,
    )
    if existing:
        return {"ok": True, "approval": existing}

    transfer_values = None
    if request.action == "transfer":
        try:
            amount = Decimal(str(request.payload.get("amount")))
        except (InvalidOperation, TypeError, ValueError):
            raise HTTPException(status_code=422, detail="Số tiền chuyển không hợp lệ.")
        from_account = request.payload.get("from_account")
        to_account = request.payload.get("to_account")
        if (
            not amount.is_finite()
            or amount <= 0
            or not isinstance(from_account, str)
            or not from_account.strip()
            or not isinstance(to_account, str)
            or not to_account.strip()
        ):
            raise HTTPException(status_code=422, detail="Thông tin chuyển khoản không hợp lệ.")
        transfer_values = (amount, from_account.strip(), to_account.strip())

    approval = storage.approve_hitl(user_id, request.idempotency_key, action)

    if request.action == "task_delete" and request.payload.get("task_id"):
        storage.delete_task(user_id, {"task_id": request.payload["task_id"]})
    elif request.action == "task_delete" and request.payload.get("title"):
        storage.delete_task(user_id, {"title": request.payload["title"]})
    elif request.action == "savings_create":
        storage.add_record("savings_goals", user_id, request.payload)
    elif request.action == "loan_apply":
        storage.add_record("plans", user_id, {**request.payload, "status": "approved"})
    elif transfer_values:
        amount, from_account, to_account = transfer_values
        storage.add_transaction(
            user_id,
            amount=amount,
            transaction_type="transfer",
            description=f"Chuyển từ {from_account} sang {to_account}",
            category="Chuyển khoản",
            account=to_account,
        )

    return {"ok": True, "approval": approval}


class ChatResponse(BaseModel):
    session_id: str
    intent: str
    confidence: float
    route: str
    status: str  # "READY", "NEED_CLARIFICATION", "BLOCKED", "FAILED"
    message: str
    reply: str  # Backwards compatibility alias
    quick_replies: list[str] = Field(default_factory=list)
    slots: dict[str, Any] = Field(default_factory=dict)
    data: dict[str, Any] | None = None
    requires_hitl: bool = False
    latency_ms: float


# ----------------- DETERMINISTIC ACTION EXECUTOR -----------------
def execute_fast_path_action(intent: str, slots: dict[str, Any], user_id: str = "default_user") -> tuple[str, dict[str, Any] | None, list[str]]:
    """Execute zero-LLM deterministic action using pure Decimal calculator or response templates.

    Returns:
        (reply_message, result_data, quick_replies)
    """
    clean_slots = {
        k: float(v) if isinstance(v, Decimal) else v
        for k, v in slots.items()
    }

    # 1. Task Domain Templates
    if intent in {"task.query_today", "task.query"}:
        tasks = storage.list_tasks(user_id, status="pending")
        return (
            f"📅 **Danh sách công việc hôm nay của bạn:** {len(tasks)} công việc đang chờ xử lý.",
            {"count": len(tasks), "tasks": tasks},
            ["Thêm việc mới", "Xem deadline tuần"],
        )

    if intent == "task.query_deadline":
        tasks = storage.list_tasks(user_id, status="pending")
        return (
            f"⏰ **Cảnh báo hạn chót (Deadline):** Có {len(tasks)} công việc đang chờ kiểm tra.",
            {"count": len(tasks), "deadlines": tasks},
            ["Đã làm xong", "Dời hạn chót", "Xem việc hôm nay"],
        )

    if intent == "task.create":
        task = storage.add_task(user_id, clean_slots)
        return template_task_create({**clean_slots, "task_id": task["id"]})

    if intent == "task.complete":
        task = storage.update_task(user_id, clean_slots, "completed")
        return template_task_complete({**clean_slots, "task_id": task.get("id") if task else clean_slots.get("task_id")})

    if intent == "task.create_recurring":
        title = clean_slots.get("title", "thói quen mới")
        recurrence = clean_slots.get("recurrence", "theo lịch đã nói")
        task = storage.add_task(user_id, {**clean_slots, "title": title, "recurrence": recurrence})
        return (
            f"✅ Đã tạo công việc lặp lại '{title}' ({recurrence}).",
            {"task": task, "recurring": True},
            ["Xem việc hôm nay", "Tạo việc khác"],
        )

    if intent == "task.query_by_tag":
        keyword = clean_slots.get("keyword", clean_slots.get("title", "nhãn đã chọn"))
        tasks = storage.list_tasks(user_id, status="all", keyword=keyword)
        return (
            f"📋 Tìm thấy {len(tasks)} công việc theo nhãn/từ khóa '{keyword}'.",
            {"filter": "tag", "keyword": keyword, "tasks": tasks},
            ["Xem tất cả việc", "Tạo việc mới"],
        )

    if intent == "task.query_completed":
        tasks = storage.list_tasks(user_id, status="completed")
        return (
            f"✅ Có {len(tasks)} công việc đã hoàn thành.",
            {"filter": "completed", "tasks": tasks},
            ["Xem việc hôm nay", "Xem việc đang chờ"],
        )

    if intent == "task.schedule_event":
        task = storage.add_task(user_id, {**clean_slots, "is_event": True})
        return (
            f"📅 Đã lên lịch '{clean_slots.get('title', 'sự kiện mới')}' vào {clean_slots.get('start_time', 'thời gian đã nói')}.",
            {"event": task},
            ["Xem lịch hôm nay", "Tạo sự kiện khác"],
        )

    if intent == "task.reschedule":
        task = storage.update_task(user_id, clean_slots, "pending")
        return (
            f"🔄 Đã dời lịch '{clean_slots.get('title', 'công việc')}' sang {clean_slots.get('new_deadline', 'thời gian mới')}.",
            {"rescheduled_task": task or clean_slots},
            ["Xem việc hôm nay", "Dời việc khác"],
        )

    if intent == "task.cancel":
        task = storage.update_task(user_id, clean_slots, "cancelled")
        return (
            f"⏸️ Đã hủy/tạm hoãn công việc '{clean_slots.get('title', 'công việc')}' và giữ lại lịch sử.",
            {"cancelled_task": task or clean_slots},
            ["Xem việc hôm nay", "Tạo việc mới"],
        )

    if intent == "task.search":
        keyword = clean_slots.get("keyword", clean_slots.get("title", ""))
        tasks = storage.list_tasks(user_id, status="all", keyword=keyword)
        return (
            f"🔎 Tìm thấy {len(tasks)} công việc theo từ khóa '{keyword}'.",
            {"filter": "search", "keyword": keyword, "tasks": tasks},
            ["Xem việc hôm nay", "Tìm từ khóa khác"],
        )

    if intent == "task.delete":
        # This branch is reached only after HITL confirmation in the API.
        deleted = storage.delete_task(user_id, clean_slots)
        return (
            f"🗑️ Đã xóa công việc '{clean_slots.get('title', clean_slots.get('task_id', 'đã chọn'))}'." if deleted else "Không tìm thấy công việc để xóa.",
            {"deleted_task": deleted, "delete_proposal": clean_slots},
            ["Xem việc hôm nay", "Tạo việc mới"],
        )

    # 2. Finance Domain Templates & Calculators
    if intent in {"finance.get_balance", "finance.balance.query"}:
        summary = storage.summary(user_id)
        return (
            f"💰 Số dư khả dụng hiện tại: {format_currency(summary['balance'])}.",
            {"summary": {key: float(value) for key, value in summary.items()}},
            ["Ghi khoản chi", "Xem lịch sử giao dịch"],
        )

    if intent == "finance.query_debt":
        debts = storage.list_records("debts", user_id)
        person = clean_slots.get("person")
        if person:
            person_lower = str(person).casefold()
            matches = [
                debt for debt in debts
                if person_lower in str(debt.get("person", "")).casefold()
            ]
            if matches:
                message = f"🧾 Hiện có {len(matches)} khoản nợ liên quan đến {person}."
            else:
                message = f"🤝 Hiện tại bạn và **{person}** không có khoản nợ nào trong sổ."
            return message, {"debts": matches, "filter": clean_slots, "count": len(matches)}, ["Xem ai nợ tôi", "Xem tôi nợ ai", "Ghi nợ mới", "Đã trả nợ"]

        total_lend = sum(
            (Decimal(str(debt.get("amount", "0"))) for debt in debts if debt.get("debt_type") == "lend"),
            Decimal("0"),
        )
        total_borrow = sum(
            (Decimal(str(debt.get("amount", "0"))) for debt in debts if debt.get("debt_type") == "borrow"),
            Decimal("0"),
        )
        return (
            f"🧾 Sổ nợ hiện có {len(debts)} khoản (cho vay: {format_currency(total_lend)}, vay: {format_currency(total_borrow)}).",
            {"debts": debts, "total_lend": float(total_lend), "total_borrow": float(total_borrow), "filter": clean_slots},
            ["Xem ai nợ tôi", "Xem tôi nợ ai", "Ghi nợ mới", "Đã trả nợ"],
        )

    if intent == "finance.split_bill":
        return template_finance_split_bill(clean_slots)

    if intent == "finance.pay_bill":
        payment = storage.add_transaction(user_id, amount=slots.get("amount", 0), transaction_type="expense", description=str(clean_slots.get("bill_name", "hóa đơn")), category="Hóa đơn", account=str(clean_slots.get("account", "default_account")))
        return (
            f"✅ Đã ghi nhận thanh toán hóa đơn {format_currency(slots.get('amount', 0))}.",
            {"bill_payment": payment},
            ["Xem số dư", "Xem lịch sử giao dịch"],
        )

    if intent in {"finance.add_expense", "finance.expense.create"}:
        amt = slots.get("amount", 0)
        note = slots.get("note") or slots.get("category", "chi tiêu")
        acc = slots.get("account", "Ví mặc định")
        transaction = storage.add_transaction(user_id, amount=amt, transaction_type="expense", description=str(note), category=str(slots.get("category", "Khác")), account=str(acc))
        formatted_amt = format_currency(amt)
        msg = f"Đã ghi nhận khoản chi {formatted_amt} cho '{note}' (Nguồn: {acc})."
        return msg, {"transaction_type": "expense", "recorded": transaction}, ["Xem số dư", "Ghi thêm khoản chi", "Lịch sử chi tiêu"]

    if intent in {"finance.add_income", "finance.income.create"}:
        amt = slots.get("amount", 0)
        source = slots.get("source", "khoản thu")
        transaction = storage.add_transaction(user_id, amount=amt, transaction_type="income", description=str(source), category="Thu nhập", account=str(slots.get("account", "default_account")))
        formatted_amt = format_currency(amt)
        msg = f"Đã ghi nhận khoản thu {formatted_amt} từ '{source}' vào tài khoản."
        return msg, {"transaction_type": "income", "recorded": transaction}, ["Xem số dư", "Ghi thêm thu nhập", "Báo cáo tài chính"]

    if intent == "finance.transfer":
        transfer = storage.add_transaction(user_id, amount=slots.get("amount", 0), transaction_type="transfer", description="Chuyển tiền", category="Chuyển khoản", account=str(clean_slots.get("to_account", "default_account")))
        return (
            f"💸 Đã chuẩn bị chuyển {format_currency(slots.get('amount', 0))} từ '{clean_slots.get('from_account', 'tài khoản nguồn')}' sang '{clean_slots.get('to_account', 'tài khoản đích')}'.",
            {"transfer": transfer, "requires_confirmation": True},
            ["Xác nhận chuyển", "Hủy bỏ"],
        )

    if intent == "finance.record_debt":
        debt = storage.add_record("debts", user_id, {**clean_slots, "amount": storage._money(slots.get("amount", 0)), "status": "open"})
        return (
            f"🧾 Đã ghi khoản nợ {format_currency(slots.get('amount', 0))} với '{clean_slots.get('person', 'người liên quan')}'.",
            {"debt": debt, "transaction_type": "debt"},
            ["Xem sổ nợ", "Ghi khoản nợ khác"],
        )

    if intent == "finance.debt_repay":
        repayment = storage.add_record("debts", user_id, {**clean_slots, "amount": storage._money(slots.get("amount", 0)), "status": "repaid"})
        return (
            f"✅ Đã ghi nhận khoản trả nợ {format_currency(slots.get('amount', 0))} cho '{clean_slots.get('person', 'người liên quan')}'.",
            {"debt_repayment": repayment},
            ["Xem sổ nợ", "Ghi khoản trả khác"],
        )

    if intent == "finance.query_transactions":
        transactions = storage.list_transactions(user_id, category=clean_slots.get("category"), keyword=clean_slots.get("keyword"))
        return (
            f"📊 Tìm thấy {len(transactions)} giao dịch.",
            {"filter": "transactions", "query": clean_slots, "transactions": transactions},
            ["Xem số dư", "Lọc khoảng thời gian khác"],
        )

    if intent in {"finance.budget_plan", "finance.update_budget"}:
        action = "thiết lập" if intent == "finance.budget_plan" else "cập nhật"
        budget = storage.add_record("budgets", user_id, {**clean_slots, "limit_amount": storage._money(slots.get("limit_amount", slots.get("amount", 0)))})
        return (
            f"📌 Đã {action} ngân sách {format_currency(slots.get('limit_amount', slots.get('amount', 0)))} cho '{clean_slots.get('category', 'tất cả danh mục')}'.",
            {"budget": budget, "requires_confirmation": True},
            ["Xem ngân sách", "Điều chỉnh ngân sách"],
        )

    if intent == "finance.savings_goal":
        goal = storage.add_record("savings_goals", user_id, {**clean_slots, "target_amount": storage._money(slots.get("target_amount", slots.get("amount", 0))), "current_amount": "0"})
        return (
            f"🎯 Đã tạo mục tiêu tiết kiệm '{clean_slots.get('goal_name', 'mục tiêu mới')}' với đích {format_currency(slots.get('target_amount', slots.get('amount', 0)))}.",
            {"savings_goal": goal, "requires_confirmation": True},
            ["Xem mục tiêu", "Tạo mục tiêu khác"],
        )

    if intent == "cross.bill_due_reminder":
        reminder = storage.add_record("reminders", user_id, clean_slots)
        return (
            f"⏰ Đã tạo nhắc hạn '{clean_slots.get('bill_name', 'hóa đơn')}' vào {clean_slots.get('due_date', 'thời hạn đã nói')}.",
            {"reminder": reminder},
            ["Xem deadline", "Tạo nhắc khác"],
        )

    if intent in {"finance.loan_installment_plan", "finance.loan.calculate"}:
        principal = slots.get("principal", 0)
        term_months = slots.get("term_months", 12)
        annual_rate = slots.get("annual_rate", 10.0)
        try:
            amortization = calculate_loan_amortization(
                principal=Decimal(str(principal)),
                annual_interest_rate=Decimal(str(annual_rate)),
                months=int(term_months),
            )
            monthly_payment = amortization.get("monthly_payment", 0)
            formatted_principal = format_currency(principal)
            formatted_monthly = format_currency(monthly_payment)
            msg = (
                f"Kế hoạch trả góp gói vay {formatted_principal} trong {term_months} tháng "
                f"(lãi suất {annual_rate}%/năm): Trả hàng tháng khoảng {formatted_monthly}."
            )
            clean_amortization = {
                k: float(v) if isinstance(v, Decimal) else v
                for k, v in amortization.items()
                if k != "schedule"
            }
            return msg, {"loan_plan": clean_amortization}, ["Xem bảng khấu hao", "Tính gói vay khác"]
        except Exception:
            return f"Đã lập kế hoạch vay {principal} trong {term_months} tháng.", {"loan": clean_slots}, []

    # 3. System Domain Templates
    if intent == "system.greeting_summary":
        summary = storage.summary(user_id)
        tasks = storage.list_tasks(user_id, status="pending")
        return (
            f"Xin chào! Số dư hiện tại là {format_currency(summary['balance'])}, bạn có {len(tasks)} việc đang chờ.",
            {"summary": {key: float(value) for key, value in summary.items()}, "pending_tasks": tasks},
            ["Xem việc hôm nay", "Xem số dư", "Báo cáo tài chính"],
        )

    if intent == "system.help":
        return template_system_help()

    if intent == "system.undo":
        return (
            "↩️ Đã tìm thao tác gần nhất và sẵn sàng hoàn tác sau khi bạn xác nhận.",
            {"undo": True, "requires_confirmation": True},
            ["Xác nhận hoàn tác", "Giữ nguyên"],
        )

    if intent == "cross.plan_expense_task":
        return (
            "🧭 Đã nhận kế hoạch công việc kèm ngân sách và chuyển sang Reasoning Path để lập phương án chi tiết.",
            {"plan": clean_slots},
            ["Lưu kế hoạch", "Tạo ngân sách"],
        )

    return f"⚠️ Intent '{intent}' chưa có executor đăng ký.", {"slots": clean_slots, "unhandled": True}, ["Trợ giúp"]


# ----------------- ENDPOINTS -----------------
@app.get("/")
def read_root():
    return {
        "service": "OnisAgent FastAPI Backend",
        "model": "Kev Decision Model (Fast Path)",
        "status": "ready" if state.kev_model else "model_not_loaded",
        "supported_intents": len(state.supported_intents),
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Check database connectivity, model state, and supported intent catalog."""
    try:
        with postgres.SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable.",
        ) from exc

    model = get_kev_model()
    return HealthResponse(
        status="ok",
        version="1.0.0",
        database_connected=True,
        model_loaded=model is not None,
        supported_intents_count=len(state.supported_intents),
        intents=state.supported_intents,
    )


@app.post("/api/v1/intent/classify", response_model=ClassifyResponse, tags=["Kev Fast Path"])
def classify_intent(request: ClassifyRequest, authorization: str | None = Header(default=None)):
    """Fast sub-10ms intent classification testing endpoint for Web UI / Diagnostics."""
    model = get_kev_model()
    _resolve_user(authorization)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kev Intent Classifier is not loaded.",
        )

    start = time.perf_counter()
    probs = model.predict_proba([request.text])[0]
    best_idx = int(np.argmax(probs))
    intent = model.classes_[best_idx]
    confidence = float(probs[best_idx])
    latency_ms = (time.perf_counter() - start) * 1000

    if _looks_like_greeting_summary(request.text):
        intent = "system.greeting_summary"
    elif _looks_like_cross_plan(request.text):
        intent = "cross.plan_expense_task"
    elif _looks_like_budget_plan(request.text):
        intent = "finance.budget_plan"
    elif _looks_like_task_plan(request.text):
        intent = "task.plan_schedule"
    elif _looks_like_task_today_query(request.text):
        intent = "task.query_today"

    # If intent belongs to Reasoning Path OR confidence is lower than threshold
    REASONING_INTENTS = {
        "finance.financial_report",
        "task.plan_schedule",
        "cross.plan_expense_task",
        "finance.budget_plan",
    }
    is_reasoning_intent = (intent in REASONING_INTENTS)
    if is_reasoning_intent or confidence < CONFIDENCE_THRESHOLD:
        route = "REASONING_PATH"
    else:
        route = "FAST_PATH"
    raw_slots = parse_slots_from_text(request.text, intent)

    return ClassifyResponse(
        intent=intent,
        confidence=round(confidence, 4),
        route=route,
        latency_ms=round(latency_ms, 2),
        raw_slots=raw_slots,
    )


@app.post("/api/v1/chat", response_model=ChatResponse, tags=["Chat Agent"])
def chat(request: ChatRequest, authorization: str | None = Header(default=None)):
    """Unified Chat Endpoint serving Flutter Web/Mobile clients.

    1. Kev Decision Classifier -> predicts intent & confidence.
    2. Heuristic/Regex Slot Extraction -> extracts raw slot values.
    3. SessionManager & SlotValidator -> handles multi-turn clarification.
    4. Fast Path Execution or Clarification Response.
    """
    model = get_kev_model()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kev Intent Classifier is not loaded.",
        )

    auth_user = _resolve_user(authorization)
    user_id = auth_user["id"] if auth_user else request.user_id

    start = time.perf_counter()
    session = state.session_manager.get_session(request.session_id, user_id)

    # 1. Inference with Kev
    probs = model.predict_proba([request.text])[0]
    best_idx = int(np.argmax(probs))
    detected_intent = model.classes_[best_idx]
    confidence = float(probs[best_idx])

    if _looks_like_greeting_summary(request.text):
        detected_intent = "system.greeting_summary"
    elif _looks_like_cross_plan(request.text):
        detected_intent = "cross.plan_expense_task"
    elif _looks_like_budget_plan(request.text):
        detected_intent = "finance.budget_plan"
    elif _looks_like_task_plan(request.text):
        detected_intent = "task.plan_schedule"
    elif _looks_like_task_today_query(request.text):
        detected_intent = "task.query_today"

    # If the session is actively waiting for clarification and confidence is borderline,
    # respect the pending intent
    if session.waiting_for_slot and confidence < 0.60:
        active_intent = session.current_intent or detected_intent
    else:
        active_intent = detected_intent

    # If intent belongs to Reasoning Path OR confidence is lower than threshold
    REASONING_INTENTS = {
        "finance.financial_report",
        "task.plan_schedule",
        "cross.plan_expense_task",
        "finance.budget_plan",
    }
    is_reasoning_intent = (active_intent in REASONING_INTENTS)
    if is_reasoning_intent or confidence < CONFIDENCE_THRESHOLD:
        route = "REASONING_PATH"
    else:
        route = "FAST_PATH"

    # 2. Extract raw slots from user input
    extracted_slots = parse_slots_from_text(request.text, active_intent)
    if request.slots:
        extracted_slots.update(request.slots)

    # If session is waiting for amount, handle pure numbers or quick reply click
    if session.waiting_for_slot == "amount" and "amount" not in extracted_slots:
        amt_match = parse_slots_from_text(f"chi {request.text}", "finance.add_expense")
        if "amount" in amt_match:
            extracted_slots["amount"] = amt_match["amount"]
        else:
            clean_num = re.sub(r"[^\d]", "", request.text)
            if clean_num:
                extracted_slots["amount"] = int(clean_num)

    # 3. Process turn with SessionManager & SlotValidator
    action_res = state.session_manager.process_turn(
        session_id=request.session_id,
        user_id=user_id,
        intent=active_intent,
        slots=extracted_slots,
    )

    latency_ms = round((time.perf_counter() - start) * 1000, 2)

    # Convert Decimals to float/str for clean JSON serialization
    serializable_slots = {
        k: float(v) if isinstance(v, Decimal) else v
        for k, v in action_res.slots.items()
    }

    # 4. Handle response states
    if action_res.status == ExecutionStatus.NEED_CLARIFICATION and route == "FAST_PATH":
        clar = action_res.clarification
        msg = clar.message if clar else "Vui lòng cung cấp thêm thông tin."
        return ChatResponse(
            session_id=request.session_id,
            intent=action_res.intent,
            confidence=round(confidence, 4),
            route=route,
            status="NEED_CLARIFICATION",
            message=msg,
            reply=msg,
            quick_replies=clar.quick_replies if clar else [],
            slots=serializable_slots,
            data=None,
            requires_hitl=False,
            latency_ms=latency_ms,
        )

    if action_res.status == ExecutionStatus.BLOCKED:
        msg = action_res.message or "Hành động này cần bạn xác nhận trước khi thực hiện."
        return ChatResponse(
            session_id=request.session_id,
            intent=action_res.intent,
            confidence=round(confidence, 4),
            route=route,
            status="BLOCKED",
            message=msg,
            reply=msg,
            quick_replies=["Xác nhận", "Hủy bỏ"],
            slots=serializable_slots,
            data=None,
            requires_hitl=True,
            latency_ms=latency_ms,
        )

    hitl_intents = {
        "finance.loan_installment_plan",
        "finance.loan.calculate",
        "finance.savings_goal",
        "finance.transfer",
    }
    if active_intent in hitl_intents and not request.user_confirmed:
        return ChatResponse(
            session_id=request.session_id,
            intent=action_res.intent,
            confidence=round(confidence, 4),
            route=route,
            status="BLOCKED",
            message="Hành động tài chính nhạy cảm cần xác nhận trực tiếp trước khi ghi dữ liệu.",
            reply="Hành động tài chính nhạy cảm cần xác nhận trực tiếp trước khi ghi dữ liệu.",
            quick_replies=["Xác nhận", "Hủy bỏ"],
            slots=serializable_slots,
            data={"requires_approval": True, "idempotency_key": request.idempotency_key},
            requires_hitl=True,
            latency_ms=latency_ms,
        )

    # 5. Reasoning Path (System 2: Ollama Local LLM)
    if route == "REASONING_PATH":
        if active_intent == "finance.budget_plan":
            storage.add_record("budgets", user_id, {**serializable_slots, "status": "pending_confirmation"})
        elif active_intent == "cross.plan_expense_task":
            storage.add_record("plans", user_id, {**serializable_slots, "status": "draft"})
        summary = storage.summary(user_id)
        pending_tasks = storage.list_tasks(user_id, status="pending")
        debts = storage.list_records("debts", user_id)
        reasoning_context = {
            "intent": active_intent,
            "confidence": round(confidence, 4),
            "slots": serializable_slots,
            "current_balance": float(summary["balance"]),
            "monthly_income": float(summary["income"]),
            "monthly_expense": float(summary["expense"]),
            "pending_tasks": pending_tasks,
            "debts": debts,
        }

        custom_system_prompt = None
        if active_intent == "cross.plan_expense_task":
            custom_system_prompt = (
                "Bạn là OnisAgent - Chuyên gia AI lập kế hoạch hành trình và phân bổ tài chính thông minh.\n"
                "Khi người dùng đưa ra dự định đi du lịch, phượt, sự kiện hoặc mua sắm gắn ngân sách dự kiến:\n"
                "1. Lập bảng phân bổ ngân sách ước tính chi tiết và thực tế (Ví dụ: Tiền xe/vé di chuyển, Khách sạn/lưu trú, Ăn uống trải nghiệm, Vé tham quan/hoạt động, và Quỹ dự phòng phát sinh ~10-15%).\n"
                "2. Đưa ra danh sách các việc cần chuẩn bị (To-do / Packing list: Đặt phòng, vé xe, tư trang cần thiết, đồ dùng cá nhân).\n"
                "3. Trình bày bằng tiếng Việt rõ ràng, dùng bullet point và emoji sinh động, tính toán khớp với tổng ngân sách dự kiến của người dùng."
            )
            reasoning_chips = ["Lưu kế hoạch", "Tạo ngân sách", "Thêm việc cần chuẩn bị"]
        else:
            reasoning_chips = ["Xem báo cáo chi tiết", "Lập kế hoạch hành động", "Đặt mục tiêu tài chính"]

        llm_reply = ollama_client.generate_reasoning_response(
            prompt=request.text,
            system_prompt=custom_system_prompt,
            context=reasoning_context,
        )

        total_latency_ms = round((time.perf_counter() - start) * 1000, 2)

        return ChatResponse(
            session_id=request.session_id,
            intent=action_res.intent,
            confidence=round(confidence, 4),
            route="REASONING_PATH",
            status="READY",
            message=llm_reply,
            reply=llm_reply,
            quick_replies=reasoning_chips,
            slots=serializable_slots,
            data={"reasoning_context": reasoning_context, "provider": "ollama", "model": ollama_client.model},
            requires_hitl=False,
            latency_ms=total_latency_ms,
        )

    # Status is READY -> Execute deterministic action
    reply_msg, reply_data, action_chips = execute_fast_path_action(action_res.intent, action_res.slots, user_id)

    return ChatResponse(
        session_id=request.session_id,
        intent=action_res.intent,
        confidence=round(confidence, 4),
        route=route,
        status="READY",
        message=reply_msg,
        reply=reply_msg,
        quick_replies=action_chips,
        slots=serializable_slots,
        data=reply_data,
        requires_hitl=action_res.requires_hitl,
        latency_ms=latency_ms,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
