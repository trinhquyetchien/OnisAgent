# Architecture Decision Records (ADRs) - OnisAgent

Hồ sơ các quyết định kiến trúc trọng yếu của hệ thống **OnisAgent** (AI Agent for Personal Task and Financial Management) chuẩn hóa theo mô hình **Single-Agent Đa luồng (Dual-Path Cognitive Architecture)**, tích hợp **Fast Path (System 1 / Kev Decision Model)**, **Reasoning Path (System 2 / Amazon Bedrock / Ollama LLM)**, **Strands Multi-Agent Swarm** và cơ chế **Voice-First**.

---

## Danh Mục Các Quyết Định Kiến Trúc (ADR Matrix)

| Mã ADR | Tiêu Đề Quyết Định Kiến Trúc | Trạng Thái | Ngày Chốt | Quyết Định Trọng Tâm |
|:---:|:---|:---:|:---:|:---|
| [**ADR-0001**](ADR-0001-decimal-money-calculation.md) | Tách suy luận LLM khỏi tính toán tài chính bằng Decimal & Thực thi trên Fast Path | `Accepted` | 2026-10-10 | Tách suy luận LLM khỏi số học; 100% phép tính dùng Python `Decimal`; tính toán tài chính xác định (số dư, phân bổ thu chi, lịch trả nợ vay, quỹ tiết kiệm) chạy trên **Fast Path (AWS Lambda)** trong **~5–12 ms, 0 Token LLM**; cấm LLM tự sinh số học. |
| [**ADR-0002**](ADR-0002-dual-path-architecture-swarm.md) | Single-Agent Dual-Path Cognitive Architecture & Multi-Agent Swarm Orchestration | `Accepted` | 2026-10-10 | Mô hình não bộ 2 hệ thống; **Decision Router & Policy Engine** với Softmax Calibrated ($T=2.35$); **Fast Path (System 1)** xử lý 85% tác vụ lặp lại; **Reasoning Path (System 2)** áp dụng Grounded Context Injection (0% ảo giác); điều phối 3 Sub-Agents chuyên biệt (`CategorizationAgent`, `FinancialAdvisoryAgent`, `TaskManagerAgent`) trên Strands SDK Swarm. |
| [**ADR-0003**](ADR-0003-dynamodb-s3-hybrid-storage.md) | Lựa chọn Cấu trúc Lưu trữ Dữ liệu Lai Amazon DynamoDB và Amazon S3 & Cơ chế Đồng bộ Cục bộ | `Accepted` | 2026-10-10 | Phân tầng lưu trữ lai: **DynamoDB** với 4 bảng chuẩn hóa (`Transactions`, `Tasks`, `Sessions`, `SavingsGoals`); **Amazon S3** lưu trữ đệm ảnh hóa đơn (Receipt Blobs) và file âm thanh đệm (**Temp Audio**) tự hủy sau 24–48h; đồng bộ dự phòng cục bộ qua `data/onis_db.json`. |
| [**ADR-0004**](ADR-0004-human-in-the-loop-workflow.md) | Thiết Lập Cơ Chế Kiểm Soát Người Dùng (Human-in-the-Loop) & 3 Chốt Phê Duyệt An Toàn (Trigger Gates) | `Accepted` | 2026-10-10 | Nguyên tắc "AI đề xuất, Người dùng quyết định" với **3 Trigger Gates**: **Gate 1** (Xác nhận áp dụng lịch trả góp khoản vay hoặc mục tiêu tiết kiệm mới), **Gate 2** (Đính chính phân loại & lưu `Correction History` cô lập theo `user_id`), **Gate 3** (Chặn và cảnh báo thao tác rủi ro cao `write_high`). |
| [**ADR-0005**](ADR-0005-voice-first-pipeline.md) | Voice-First Two-Way Vietnamese Speech Pipeline (STT/TTS) | `Accepted` | 2026-10-15 | Giao tiếp hai chiều bằng giọng nói tiếng Việt tự nhiên; hỗ trợ linh hoạt 2 chế độ **Click-to-Talk** & **Push-to-Talk**; Web Speech API / Whisper (STT) + Neural TTS; **ngân sách độ trễ âm thanh $\le 2$ giây**; chuẩn hóa tiếng lóng tài chính Việt Nam. |

---

## Nguyên Tắc Cốt Lõi (Core Principles)

1. **"Models reason, software computes"** (Mô hình suy luận, phần mềm tính toán).
2. **"AI Proposes, Human Disposes"** (AI đề xuất, Con người quyết định).
3. **"Zero-Friction Voice-First"** (Tương tác giọng nói tiếng Việt rảnh tay, triệt tiêu ma sát nhập liệu).
4. **"Dual-Path Cognitive Routing"** (Phản xạ tức thì 5–12ms cho tác vụ đơn giản, suy luận sâu không ảo giác cho tác vụ phức tạp).
