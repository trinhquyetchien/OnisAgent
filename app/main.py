import hashlib
import io
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

_tts_cache: Dict[str, bytes] = {}

from . import db
from .config import BASE_DIR, DATA_FILE, KEV_BASE_URL, KEV_MODEL_NAME
from .kev_client import build_systemone_request, evaluate_system1, predict_embedded_kev
from .ollama_client import get_active_model, get_available_models, set_active_model
from .router import process_user_request
from .tools import FinanceTools, TaskTools, SavingsTools, ReminderTools, MemoryTools

app = FastAPI(title="OnisAgent Demo API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = BASE_DIR / "static"
db.init_db()


class ChatRequest(BaseModel):
    text: str


class ModelSelectRequest(BaseModel):
    model: str


class AddTxRequest(BaseModel):
    type: str  # "expense" or "income"
    amount: float
    category: str
    description: str


class AddTaskRequest(BaseModel):
    title: str
    deadline: Optional[str] = None
    priority: str = "medium"


class AddGoalRequest(BaseModel):
    name: str
    target_amount: float
    deadline: Optional[str] = None


class DepositGoalRequest(BaseModel):
    goal_id: str
    amount: float


class AddReminderRequest(BaseModel):
    text: str
    remind_at: Optional[str] = None


class AddNoteRequest(BaseModel):
    content: str
    category: str = "general"


class LoanCalcRequest(BaseModel):
    principal: float
    annual_rate_pct: float = 10.0
    months: int = 12


class SetBudgetRequest(BaseModel):
    monthly_limit: float


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Nội dung không được để trống")
    
    res = await process_user_request(req.text)
    
    # Attach fresh database snapshots for real-time frontend update
    res["db_summary"] = {
        "finance": db.get_finance_summary(),
        "tasks": TaskTools.get_tasks(),
        "savings": SavingsTools.get_goals(),
        "reminders": ReminderTools.get_reminders(),
        "notes": MemoryTools.get_notes()
    }
    return res


@app.get("/api/models")
async def models_endpoint():
    ollama_models = await get_available_models()
    active_llm = get_active_model()
    
    return {
        "sys1": {
            "name": KEV_MODEL_NAME,
            "provider": "Kev Decision Model (jaredpalmer/kev)",
            "status": "ready",
            "spec": "TypeSafe /v1/systemone"
        },
        "llm": {
            "active": active_llm,
            "available": ollama_models,
            "provider": "Ollama Local Inference"
        }
    }


@app.post("/api/models/select")
async def select_model_endpoint(req: ModelSelectRequest):
    new_model = set_active_model(req.model)
    return {"status": "ok", "active_model": new_model}


@app.get("/api/data")
async def get_raw_data():
    return db.load_db()


@app.post("/api/data/reset")
async def reset_data():
    db.reset_to_default()
    return {"status": "ok", "message": "Đã reset dữ liệu về trạng thái ban đầu"}


@app.get("/api/finance/summary")
async def get_finance_summary():
    return FinanceTools.get_summary()


@app.get("/api/finance/transactions")
async def get_finance_transactions():
    return FinanceTools.get_transactions(limit=50)


@app.post("/api/finance/add")
async def add_transaction_endpoint(req: AddTxRequest):
    if req.type == "expense":
        return FinanceTools.create_expense(req.amount, req.category, req.description, created_by="web_dashboard")
    else:
        return FinanceTools.create_income(req.amount, req.category, req.description, created_by="web_dashboard")


@app.delete("/api/finance/{tx_id}")
async def delete_tx_endpoint(tx_id: str):
    success = db.delete_transaction(tx_id)
    return {"success": success}


@app.get("/api/tasks")
async def get_tasks_endpoint():
    return TaskTools.get_tasks()


@app.post("/api/tasks/toggle/{task_id}")
async def toggle_task_endpoint(task_id: str):
    res = db.toggle_task(task_id)
    if res:
        return {"success": True, "task": res}
    raise HTTPException(status_code=404, detail="Task not found")


@app.post("/api/tasks/add")
async def add_task_endpoint(req: AddTaskRequest):
    return TaskTools.create_task(req.title, req.deadline, req.priority)


@app.delete("/api/tasks/{task_id}")
async def delete_task_endpoint(task_id: str):
    return TaskTools.delete_task(task_id)


# --- Savings Endpoints ---
@app.get("/api/savings/goals")
async def get_savings_goals_endpoint():
    return SavingsTools.get_goals()


@app.post("/api/savings/goals")
async def add_savings_goal_endpoint(req: AddGoalRequest):
    return SavingsTools.add_goal(req.name, req.target_amount, req.deadline)


@app.post("/api/savings/deposit")
async def deposit_savings_goal_endpoint(req: DepositGoalRequest):
    return SavingsTools.deposit(req.goal_id, req.amount)


@app.delete("/api/savings/goals/{goal_id}")
async def delete_savings_goal_endpoint(goal_id: str):
    return SavingsTools.delete_goal(goal_id)


# --- Reminders Endpoints ---
@app.get("/api/reminders")
async def get_reminders_endpoint():
    return ReminderTools.get_reminders()


@app.post("/api/reminders")
async def add_reminder_endpoint(req: AddReminderRequest):
    return ReminderTools.create_reminder(req.text, req.remind_at)


@app.delete("/api/reminders/{rem_id}")
async def delete_reminder_endpoint(rem_id: str):
    return ReminderTools.delete_reminder(rem_id)


# --- Memory / Notes Endpoints ---
@app.get("/api/notes")
async def get_notes_endpoint():
    return MemoryTools.get_notes()


@app.post("/api/notes")
async def add_note_endpoint(req: AddNoteRequest):
    return MemoryTools.save_note(req.content, req.category)


# --- Extended Finance Endpoints ---
@app.get("/api/finance/budget")
async def get_budget_endpoint():
    return FinanceTools.get_budget()


@app.post("/api/finance/budget/set")
async def set_budget_endpoint(req: SetBudgetRequest):
    return FinanceTools.set_monthly_budget(req.monthly_limit)


@app.post("/api/finance/loan/calculate")
async def calculate_loan_endpoint(req: LoanCalcRequest):
    return FinanceTools.calculate_loan(req.principal, req.annual_rate_pct, req.months)


@app.post("/v1/systemone")
async def systemone_direct(req: Dict[str, Any]):
    """Direct TypeSafe /v1/systemone Kev compatibility endpoint."""
    state = req.get("state", "")
    return predict_embedded_kev(str(state))


@app.get("/api/voice/tts")
@app.head("/api/voice/tts")
async def get_vietnamese_tts(text: str):
    """Generates natural, fluent Vietnamese audio speech."""
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    cleaned = re.sub(r"\[(?:System 1 Fast Path|LLM Reasoning Path)[^\]]*\]", "", text)
    cleaned = re.sub(r"[\*#`•~_]", "", cleaned)
    cleaned = re.sub(r"⚡|🧠|⚠️|🛡️|💰|💸|🎙️", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    
    if len(cleaned) > 500:
        cleaned = cleaned[:500] + "..."
        
    cache_key = hashlib.md5(cleaned.encode("utf-8")).hexdigest()
    if cache_key in _tts_cache:
        return Response(content=_tts_cache[cache_key], media_type="audio/mpeg")
        
    try:
        from gtts import gTTS
        fp = io.BytesIO()
        tts = gTTS(text=cleaned, lang="vi", slow=False)
        tts.write_to_fp(fp)
        audio_bytes = fp.getvalue()
        if len(_tts_cache) < 200:
            _tts_cache[cache_key] = audio_bytes
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")


@app.get("/favicon.ico")
async def favicon():
    return Response(content=b"", media_type="image/x-icon")


# Serve static files and UI
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
@app.head("/")
async def root():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "OnisAgent API is running. UI not found."}
