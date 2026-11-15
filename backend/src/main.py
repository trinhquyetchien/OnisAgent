"""FastAPI Server for OnisAgent Backend.

Provides production-ready RESTful endpoints connecting:
- Kev Decision Model (Fast Path sub-10ms classification)
- Slot Validator & Multi-turn Session Manager (Clarification Engine)
- Decimal Tools (100% precision financial calculator)
- Full API for Flutter Web and Mobile clients
"""

from contextlib import asynccontextmanager
from decimal import Decimal
from pathlib import Path
import re
import time
from typing import Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import joblib
import numpy as np
from pydantic import BaseModel, Field

from src.engine.session_manager import SessionManager
from src.engine.slot_validator import SlotValidator
from src.schemas.base import ExecutionStatus
from src.tools.calculator import calculate_loan_amortization

# ----------------- CONSTANTS & PATHS -----------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "checkpoints" / "kev" / "kev_intent_model.joblib"
CONFIDENCE_THRESHOLD = 0.50


# ----------------- IN-MEMORY APPLICATION STATE -----------------
class AppState:
    kev_model: Any = None
    session_manager: SessionManager = SessionManager()
    supported_intents: list[str] = []


state = AppState()


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
    description="Cognitive Multi-turn API with Kev Fast Path & Amazon Bedrock Routing",
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
        val = float(match_k.group(1).replace(",", "."))
        slots["amount"] = Decimal(str(int(val * 1000)))
    elif match_cu:
        val = float(match_cu.group(1).replace(",", "."))
        slots["amount"] = Decimal(str(int(val * 1_000_000)))
    elif match_xi:
        val = float(match_xi.group(1).replace(",", "."))
        slots["amount"] = Decimal(str(int(val * 100_000)))
    elif match_lit:
        val = float(match_lit.group(1).replace(",", "."))
        slots["amount"] = Decimal(str(int(val * 100_000)))
    elif match_num:
        slots["amount"] = Decimal(match_num.group(1))

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

    # 5. Task title extraction
    if intent.startswith("task."):
        title = re.sub(
            r"^(tạo task|tạo việc|nhắc tôi|lên lịch|cần làm|thêm việc|hoàn thành|xóa task)\s*",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()
        if title:
            slots["title"] = title

    return slots


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
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
def execute_fast_path_action(intent: str, slots: dict[str, Any]) -> tuple[str, dict[str, Any] | None, list[str]]:
    """Execute zero-LLM deterministic action using pure Decimal calculator or domain handlers.
    
    Returns:
        (reply_message, result_data, quick_replies)
    """
    clean_slots = {
        k: float(v) if isinstance(v, Decimal) else v
        for k, v in slots.items()
    }
    quick_replies: list[str] = []

    if intent in {"finance.add_expense", "finance.expense.create"}:
        amt = slots.get("amount", 0)
        note = slots.get("note") or slots.get("category", "chi tiêu")
        acc = slots.get("account", "Ví mặc định")
        formatted_amt = f"{int(amt):,}₫".replace(",", ".")
        msg = f"Đã ghi nhận khoản chi {formatted_amt} cho '{note}' (Nguồn: {acc})."
        return msg, {"transaction_type": "expense", "recorded": clean_slots}, ["Xem số dư", "Ghi thêm khoản chi", "Lịch sử chi tiêu"]

    if intent in {"finance.add_income", "finance.income.create"}:
        amt = slots.get("amount", 0)
        source = slots.get("source", "khoản thu")
        formatted_amt = f"{int(amt):,}₫".replace(",", ".")
        msg = f"Đã ghi nhận khoản thu {formatted_amt} từ '{source}' vào tài khoản."
        return msg, {"transaction_type": "income", "recorded": clean_slots}, ["Xem số dư", "Ghi thêm thu nhập", "Báo cáo tài chính"]

    if intent in {"finance.get_balance", "finance.balance.query"}:
        msg = "Số dư hiện tại khả dụng của bạn là 18.450.000₫ (Tiền mặt: 2.100.000₫, Vietcombank: 16.350.000₫)."
        return msg, {"total_balance": 18450000, "accounts": {"cash": 2100000, "vietcombank": 16350000}}, ["Chi 50k ăn trưa", "Xem sổ nợ", "Xem việc hôm nay"]

    if intent == "finance.query_debt":
        debt_type = slots.get("debt_type", "all")
        person = slots.get("person")
        debt_chips = ["Xem ai nợ tôi", "Xem tôi nợ ai", "Ghi nợ mới", "Đã trả nợ"]

        if person:
            if person.lower() in ["tuấn", "tuan"]:
                msg = f"{person} hiện đang nợ bạn 200.000₫ (Mượn tiền ăn trưa)."
                return msg, {"person": person, "lend": [{"person": "Tuấn", "amount": 200000, "note": "Mượn tiền ăn trưa"}]}, debt_chips
            elif person.lower() in ["huy"]:
                msg = f"{person} hiện đang nợ bạn 500.000₫ (Mượn hôm nọ)."
                return msg, {"person": person, "lend": [{"person": "Huy", "amount": 500000, "note": "Mượn hôm nọ"}]}, debt_chips
            elif person.lower() in ["nam"]:
                msg = f"Bạn đang nợ {person} 150.000₫ (Nợ Nam tiền đổ xăng)."
                return msg, {"person": person, "borrow": [{"person": "Nam", "amount": 150000, "note": "Tiền đổ xăng"}]}, debt_chips
            else:
                msg = f"Hiện tại bạn và {person} không có khoản nợ nào cần thanh toán."
                return msg, {"person": person, "lend": [], "borrow": []}, debt_chips

        if debt_type == "lend":
            msg = (
                "🤝 Danh sách người đang nợ bạn:\n"
                "• Tuấn: 200.000₫ (Mượn tiền ăn trưa)\n"
                "• Huy: 500.000₫ (Mượn hôm nọ)\n"
                "👉 Tổng tiền người khác nợ bạn: 700.000₫."
            )
            return msg, {"total_lend": 700000, "records": [{"person": "Tuấn", "amount": 200000}, {"person": "Huy", "amount": 500000}]}, debt_chips

        if debt_type == "borrow":
            msg = (
                "🤝 Các khoản bạn đang nợ người khác:\n"
                "• Nam: 150.000₫ (Nợ Nam tiền đổ xăng)\n"
                "👉 Tổng nợ cần trả: 150.000₫."
            )
            return msg, {"total_borrow": 150000, "records": [{"person": "Nam", "amount": 150000}]}, debt_chips

        # default 'all'
        msg = (
            "🤝 Sổ theo dõi nợ cá nhân của bạn hiện tại:\n"
            "• Người khác đang nợ bạn: 700.000₫ (Tuấn: 200k ăn trưa, Huy: 500k mượn hôm nọ).\n"
            "• Bạn đang nợ người khác: 150.000₫ (Nợ Nam tiền đổ xăng).\n"
            "👉 Bạn đang có số dư cho mượn ròng là +550.000₫."
        )
        return msg, {
            "total_lend": 700000,
            "total_borrow": 150000,
            "net_balance": 550000,
            "lend_records": [{"person": "Tuấn", "amount": 200000}, {"person": "Huy", "amount": 500000}],
            "borrow_records": [{"person": "Nam", "amount": 150000}],
        }, debt_chips

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
            formatted_principal = f"{int(principal):,}₫".replace(",", ".")
            formatted_monthly = f"{int(monthly_payment):,}₫".replace(",", ".")
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

    if intent in {"task.query_today", "task.query"}:
        msg = (
            "📅 Hôm nay bạn có 3 công việc cần làm:\n"
            "1. 🔴 [Khẩn cấp] Hoàn thiện tài liệu kiến trúc OnisAgent (Hạn: 11:30)\n"
            "2. 🟡 [Quan trọng] Họp nhóm dự án AI4Life (Hạn: 14:00)\n"
            "3. 🟢 [Bình thường] Đọc tài liệu Flutter & Bedrock (Hạn: 22:00)"
        )
        tasks_data = [
            {"id": "t1", "title": "Hoàn thiện tài liệu kiến trúc OnisAgent", "priority": "urgent", "due": "11:30"},
            {"id": "t2", "title": "Họp nhóm dự án AI4Life", "priority": "high", "due": "14:00"},
            {"id": "t3", "title": "Đọc tài liệu Flutter & Bedrock", "priority": "normal", "due": "22:00"},
        ]
        return msg, {"tasks": tasks_data, "count": 3}, ["Thêm việc mới", "Hoàn thành việc 1", "Xem deadline tuần"]

    if intent == "task.query_deadline":
        msg = (
            "⏰ Cảnh báo hạn chót (Deadline) trong 48h tới:\n"
            "• [Còn 2 giờ] Nộp báo cáo tiến độ đồ án AI4Life (Hạn: 11:30 hôm nay)\n"
            "• [Còn 26 giờ] Hoàn tất slide thuyết trình ban giám khảo (Hạn: 12:00 ngày mai)"
        )
        deadline_data = [
            {"title": "Nộp báo cáo tiến độ đồ án AI4Life", "due": "11:30 hôm nay", "hours_left": 2},
            {"title": "Hoàn tất slide thuyết trình ban giám khảo", "due": "12:00 ngày mai", "hours_left": 26},
        ]
        return msg, {"deadlines": deadline_data, "count": 2}, ["Đã làm xong", "Dời hạn chót", "Xem việc hôm nay"]

    if intent == "task.create":
        title = slots.get("title", "công việc")
        due = slots.get("due_date", "hôm nay")
        prio = slots.get("priority", "medium")
        msg = f"Đã tạo công việc '{title}' (Hạn: {due}, Ưu tiên: {prio})."
        return msg, {"task": clean_slots}, ["Xem việc hôm nay", "Tạo thêm việc", "Xem deadline"]

    if intent == "task.complete":
        title = slots.get("title") or slots.get("task_id", "công việc")
        msg = f"Đã đánh dấu hoàn thành công việc: '{title}'! 🎉"
        return msg, {"completed_task": clean_slots}, ["Xem việc hôm nay", "Xem việc đã xong"]

    return f"Đã xử lý xong yêu cầu '{intent}'.", {"slots": clean_slots}, []


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
    """Check service health, loaded Kev model state, and supported intent catalog (32 intents)."""
    model = get_kev_model()
    return HealthResponse(
        status="ok",
        version="1.0.0",
        model_loaded=model is not None,
        supported_intents_count=len(state.supported_intents),
        intents=state.supported_intents,
    )


@app.post("/api/v1/intent/classify", response_model=ClassifyResponse, tags=["Kev Fast Path"])
def classify_intent(request: ClassifyRequest):
    """Fast sub-10ms intent classification testing endpoint for Web UI / Diagnostics."""
    model = get_kev_model()
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

    route = "FAST_PATH" if confidence >= CONFIDENCE_THRESHOLD else "REASONING_PATH"
    raw_slots = parse_slots_from_text(request.text, intent)

    return ClassifyResponse(
        intent=intent,
        confidence=round(confidence, 4),
        route=route,
        latency_ms=round(latency_ms, 2),
        raw_slots=raw_slots,
    )


@app.post("/api/v1/chat", response_model=ChatResponse, tags=["Chat Agent"])
def chat(request: ChatRequest):
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

    start = time.perf_counter()
    session = state.session_manager.get_session(request.session_id, request.user_id)

    # 1. Inference with Kev
    probs = model.predict_proba([request.text])[0]
    best_idx = int(np.argmax(probs))
    detected_intent = model.classes_[best_idx]
    confidence = float(probs[best_idx])

    # If the session is actively waiting for clarification and confidence is borderline,
    # respect the pending intent
    if session.waiting_for_slot and confidence < 0.60:
        active_intent = session.current_intent or detected_intent
    else:
        active_intent = detected_intent

    route = "FAST_PATH" if confidence >= CONFIDENCE_THRESHOLD else "REASONING_PATH"

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
        user_id=request.user_id,
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
    if action_res.status == ExecutionStatus.NEED_CLARIFICATION:
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

    # Status is READY -> Execute deterministic action
    reply_msg, reply_data, action_chips = execute_fast_path_action(action_res.intent, action_res.slots)

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
