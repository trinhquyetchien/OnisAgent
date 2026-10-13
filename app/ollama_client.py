import time
from typing import Any, Dict, List, Optional
import httpx
from .config import OLLAMA_BASE_URL, DEFAULT_OLLAMA_MODEL

CURRENT_MODEL = DEFAULT_OLLAMA_MODEL


async def get_available_models() -> List[str]:
    """Queries Ollama for list of installed models."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name") for m in data.get("models", []) if "name" in m]
                return models
    except Exception:
        pass
    return [DEFAULT_OLLAMA_MODEL]


def set_active_model(model_name: str) -> str:
    global CURRENT_MODEL
    CURRENT_MODEL = model_name
    return CURRENT_MODEL


def get_active_model() -> str:
    return CURRENT_MODEL


async def generate_reasoning(prompt: str, context_data: Optional[Dict[str, Any]] = None, custom_system_prompt: Optional[str] = None) -> Dict[str, Any]:
    """
    Sends request to Ollama LLM for reasoning, analysis or planning.
    """
    global CURRENT_MODEL
    start_time = time.perf_counter()
    
    system_instruction = (
        custom_system_prompt or (
            "Bạn là OnisAgent - Trợ lý thông minh kết hợp quản lý tài chính và công việc cá nhân. "
            "Bạn đang xử lý ở nhánh Suy luận chuyên sâu (Reasoning Path - System 2). "
            "Dựa trên dữ liệu thực tế được cung cấp, hãy phân tích một cách chính xác, sắc bén, khách quan và đưa ra lời khuyên thực tế. "
            "QUY TẮC BẮT BUỘC:\n"
            "1. Tuyệt đối không tự bịa đặt số liệu tài chính; chỉ sử dụng số liệu có trong ngữ cảnh.\n"
            "2. Trả lời bằng tiếng Việt tự nhiên, thân thiện, rõ ràng, gãy gọn, dùng định dạng Markdown đẹp.\n"
            "3. Khi phân tích chi tiêu hoặc lập kế hoạch, luôn nêu rõ các bước cụ thể tiếp theo người dùng nên làm."
        )
    )
    
    context_str = ""
    if context_data:
        context_str = f"\n\n--- DỮ LIỆU THỰC TẾ TỪ CÔNG CỤ ONISAGENT ---\n{context_data}\n---------------------------------------\n"
        
    full_prompt = f"{context_str}Yêu cầu của người dùng: {prompt}\n\nHãy phản hồi ngắn gọn, súc tích và có căn cứ:"
    
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": CURRENT_MODEL,
                    "prompt": full_prompt,
                    "system": system_instruction,
                    "stream": False,
                    "options": {
                        "temperature": 0.4,
                        "top_p": 0.9
                    }
                }
            )
            
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "text": data.get("response", "").strip(),
                    "model": CURRENT_MODEL,
                    "latency_ms": latency_ms,
                    "eval_count": data.get("eval_count", 0),
                    "prompt_eval_count": data.get("prompt_eval_count", 0),
                    "success": True
                }
            else:
                return {
                    "text": f"Lỗi từ Ollama: HTTP {resp.status_code} - {resp.text}",
                    "model": CURRENT_MODEL,
                    "latency_ms": latency_ms,
                    "success": False
                }
    except Exception as e:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "text": f"Không thể kết nối đến Ollama model '{CURRENT_MODEL}' ({str(e)}). Vui lòng đảm bảo dịch vụ Ollama đang chạy.",
            "model": CURRENT_MODEL,
            "latency_ms": latency_ms,
            "success": False
        }
