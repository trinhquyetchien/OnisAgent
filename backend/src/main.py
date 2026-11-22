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
import unicodedata
from typing import Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import joblib
import numpy as np
from pydantic import BaseModel, Field

from src.agents.ollama_client import ollama_client
from src.engine.response_templates import (
    format_currency,
    template_finance_balance,
    template_finance_pay_bill,
    template_finance_query_debt,
    template_finance_split_bill,
    template_system_greeting_summary,
    template_system_help,
    template_task_create,
    template_task_complete,
    template_task_query_deadline,
    template_task_query_today,
)
from src.engine.session_manager import SessionManager
from src.engine.slot_validator import SlotValidator
from src.schemas.base import ExecutionStatus
from src.tools.calculator import calculate_loan_amortization

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
        return template_task_query_today()

    if intent == "task.query_deadline":
        return template_task_query_deadline()

    if intent == "task.create":
        return template_task_create(clean_slots)

    if intent == "task.complete":
        return template_task_complete(clean_slots)

    # 2. Finance Domain Templates & Calculators
    if intent in {"finance.get_balance", "finance.balance.query"}:
        return template_finance_balance()

    if intent == "finance.query_debt":
        return template_finance_query_debt(clean_slots)

    if intent == "finance.split_bill":
        return template_finance_split_bill(clean_slots)

    if intent == "finance.pay_bill":
        return template_finance_pay_bill(clean_slots)

    if intent in {"finance.add_expense", "finance.expense.create"}:
        amt = slots.get("amount", 0)
        note = slots.get("note") or slots.get("category", "chi tiêu")
        acc = slots.get("account", "Ví mặc định")
        formatted_amt = format_currency(amt)
        msg = f"Đã ghi nhận khoản chi {formatted_amt} cho '{note}' (Nguồn: {acc})."
        return msg, {"transaction_type": "expense", "recorded": clean_slots}, ["Xem số dư", "Ghi thêm khoản chi", "Lịch sử chi tiêu"]

    if intent in {"finance.add_income", "finance.income.create"}:
        amt = slots.get("amount", 0)
        source = slots.get("source", "khoản thu")
        formatted_amt = format_currency(amt)
        msg = f"Đã ghi nhận khoản thu {formatted_amt} từ '{source}' vào tài khoản."
        return msg, {"transaction_type": "income", "recorded": clean_slots}, ["Xem số dư", "Ghi thêm thu nhập", "Báo cáo tài chính"]

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
        return template_system_greeting_summary()

    if intent == "system.help":
        return template_system_help()

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
    """Check service health, loaded Kev model state, and supported intent catalog."""
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

    if _looks_like_task_today_query(request.text):
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

    if _looks_like_task_today_query(request.text):
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

    # 5. Reasoning Path (System 2: Ollama Local LLM)
    if route == "REASONING_PATH":
        reasoning_context = {
            "intent": active_intent,
            "confidence": round(confidence, 4),
            "slots": serializable_slots,
            "current_balance": 18450000,
            "monthly_income": 20000000,
            "monthly_expense": 11000000,
            "pending_tasks": [
                {"title": "Hoàn thiện tài liệu OnisAgent", "due": "11:30 hôm nay", "priority": "urgent"},
                {"title": "Họp nhóm AI4Life", "due": "14:00 hôm nay", "priority": "high"},
            ],
            "debts": {
                "others_owe_me": 700000,
                "i_owe_others": 150000,
            },
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
