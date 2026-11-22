# AI Integration

## Kev Fast Path

Checkpoint: `backend/models/checkpoints/kev/kev_intent_model.joblib`.

- Load một lần trong application lifespan.
- Classify intent và confidence.
- Trích slot bằng preprocessing nhất quán với catalog.
- Sử dụng deterministic Decimal calculator cho nghiệp vụ tài chính.

## Reasoning Path

Hệ thống có thể dùng Ollama qua `OLLAMA_BASE_URL` và `OLLAMA_MODEL`. Reasoning Path không thay thế model Kev và không được phép thực hiện phép tính tài chính bằng LLM.

## Guardrails

- Thiếu slot: `NEED_CLARIFICATION`.
- Thao tác nhạy cảm: `BLOCKED`.
- Loan, savings, transfer chỉ ghi sau xác nhận người dùng.
- Xóa task hàng loạt hoặc task phá hủy yêu cầu HITL approval.
