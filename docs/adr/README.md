# Architecture Decision Records (ADRs) - OnisAgent

Hồ sơ các quyết định kiến trúc trọng yếu của hệ thống **OnisAgent** (AI Agent for Personal Task and Financial Management) chuẩn hóa theo mô hình **Single-Agent Đa luồng (Dual-Path Cognitive Architecture)**, tích hợp **Fast Path (System 1 / Kev Decision Model)**, **Reasoning Path (System 2 / Amazon Bedrock / Ollama LLM)**, **Strands Multi-Agent Swarm** và cơ chế **Voice-First**.

---

## Danh Mục Các Quyết Định Kiến Trúc (ADR Matrix)

| Mã ADR | Tiêu Đề Quyết Định Kiến Trúc | Trạng Thái | Ngày Chốt | Quyết Định Trọng Tâm |
|:---:|:---|:---:|:---:|:---|
| [**ADR-0001**](ADR-0001-decimal-money-calculation.md) | Kiểm thử Decimal cho Máy tính khoản vay dư nợ giảm dần & Số dư sổ cái | `Accepted` | 2026-10-10 | Dùng Python `Decimal` để kiểm thử chính xác số dư sổ cái và lịch trả góp gốc + lãi; calculator chạy trên AWS Lambda, không giao số học cho LLM. |
| [**ADR-0002**](ADR-0002-dual-path-architecture-swarm.md) | Single-Agent Dual-Path Cognitive Architecture & Multi-Agent Swarm Orchestration | `Accepted` | 2026-10-10 | **Fast Path (Kev Model)**: ~5–12 ms, 0 Token LLM cho khoảng 85% tác vụ lặp lại; **Reasoning Path (Amazon Bedrock / Ollama)**: phân tích dòng tiền, dự toán khoản vay, lập kế hoạch ngày/tuần; điều phối 3 Sub-Agents qua Strands SDK Swarm. |
| [**ADR-0003**](ADR-0003-dynamodb-s3-hybrid-storage.md) | DynamoDB Schema (Transactions, Tasks, Sessions, SavingsGoals) & S3 Blob Storage | `Accepted` | 2026-10-10 | Bốn nhóm dữ liệu DynamoDB (`Transactions`, `Tasks`, `Sessions`, `SavingsGoals`) cùng Amazon S3 cho ảnh hóa đơn và file âm thanh tạm; đồng bộ dự phòng cục bộ qua `data/onis_db.json`. |
| [**ADR-0004**](ADR-0004-human-in-the-loop-workflow.md) | Human-in-the-Loop (HITL) & 3 Chốt Duyệt Cho Thao Tác Nhạy Cảm | `Accepted` | 2026-10-10 | **Gate 1** xác nhận lịch vay/quỹ tiết kiệm; **Gate 2** ghi nhận đính chính phân loại; **Gate 3** chặn thao tác rủi ro cao `write_high` cho tới khi người dùng xác nhận. |
| [**ADR-0005**](ADR-0005-voice-first-pipeline.md) | Voice-First Two-Way Vietnamese Speech Pipeline (STT/TTS) | `Accepted` | 2026-10-15 | Giao tiếp hai chiều bằng giọng nói tiếng Việt tự nhiên; hỗ trợ linh hoạt 2 chế độ **Click-to-Talk** & **Push-to-Talk**; Web Speech API / Whisper (STT) + Neural TTS; **ngân sách độ trễ âm thanh $\le 2$ giây**; chuẩn hóa tiếng lóng tài chính Việt Nam. |

---

## Nguyên Tắc Cốt Lõi (Core Principles)

1. **"Models reason, software computes"** (Mô hình suy luận, phần mềm tính toán).
2. **"AI Proposes, Human Disposes"** (AI đề xuất, Con người quyết định).
3. **"Zero-Friction Voice-First"** (Tương tác giọng nói tiếng Việt rảnh tay, triệt tiêu ma sát nhập liệu).
4. **"Dual-Path Cognitive Routing"** (Phản xạ tức thì 5–12ms cho tác vụ đơn giản, suy luận sâu không ảo giác cho tác vụ phức tạp).
