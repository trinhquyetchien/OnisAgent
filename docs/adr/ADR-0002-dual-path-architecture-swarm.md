---
id: ADR-0002
timestamp: 2026-10-10T00:00:00Z
status: accepted
deciders: Trịnh Quyết Chiến, Hứa Huỳnh Anh
tags:
  - onisagent
  - aws
  - agentic-ai
  - dual-path
  - cognitive-architecture
  - system-1
  - system-2
  - kev-model
  - strands-sdk
  - multi-agent
  - swarm
  - bedrock
  - ollama
  - task-management
  - personal-finance
related_adrs: [ADR-0001, ADR-0003, ADR-0004, ADR-0005]
---

# ADR-0002: Single-Agent Dual-Path Cognitive Architecture & Multi-Agent Swarm Orchestration

> **Y-Statement:** Trong ngữ cảnh OnisAgent cần giải quyết đồng thời bài toán phân mảnh dữ liệu (tài chính – công việc) và ma sát nhập liệu thủ công (khiến hơn 85% người dùng từ bỏ ứng dụng), đồng thời vượt qua "bẫy LLM" (độ trễ 1.500–4.000 ms, chi phí token đắt đỏ và rủi ro ảo giác số học), chúng tôi quyết định chuẩn hóa mô hình **Single-Agent Nhận thức Đa luồng (Dual-Path Cognitive Architecture)** kết hợp điều phối **Multi-Agent Swarm (Strands Agents SDK)**. Hệ thống sử dụng một **Decision Router & Policy Engine** làm cổng điều phối tập trung duy nhất:
> 1. **Fast Path (System 1 / Kev Decision Model):** Xử lý phản xạ tức thì khoảng 85% tác vụ lặp lại (`transaction.create_expense`, `transaction.create_income`, `transaction.query`, `task.create`, `task.complete`) với độ trễ mục tiêu **~5–12 ms**, **0 Token LLM**, và ngưỡng tin cậy $\text{Confidence} \ge 0.65$.
> 2. **Reasoning Path (System 2 / Amazon Bedrock / Ollama LLM):** Phân tích dòng tiền sâu, dự toán khoản vay và lập kế hoạch ngày/tuần; áp dụng **Grounded Context Injection** với dữ liệu thực tế. Các con số về số dư và lịch vay luôn do phần mềm `Decimal` tính, không do LLM suy ra.
> Khi luồng Reasoning yêu cầu phân tách miền nghiệp vụ chuyên sâu, **Strands Agents SDK** điều phối Swarm gồm 3 Sub-Agents chuyên biệt (`CategorizationAgent`, `FinancialAdvisoryAgent`, `TaskManagerAgent`), giúp giảm 40% dung lượng Prompt Token và ngăn ngừa triệt để hiện tượng Tool Misfire.

---

### 1. Problem Statement & Architectural Intent (Bài toán & Ý tưởng Kiến trúc)

**Bài toán (Context):**
1. **Phân mảnh dữ liệu & Ma sát nhập liệu:**
   - Người dùng phải sử dụng riêng lẻ ứng dụng quản lý chi tiêu (Money Lover, Spendee), ứng dụng to-do list (Todoist, Notion) và ứng dụng ghi chú (Google Keep, Apple Notes). Việc thiếu không gian hợp nhất (Unified Life Workspace) làm mất liên kết giữa thời gian, ngân sách và mục tiêu cá nhân.
   - Thao tác ghi nhận một khoản chi nhỏ (ví dụ: "phở 45k" hay "tiền điện") đòi hỏi từ 6 đến 8 bước chạm thủ công trên màn hình, khiến hơn 85% người dùng bỏ cuộc sau 1–2 tuần.
2. **Nghịch lý "Bẫy LLM" (LLM Overkill & Hallucination):**
   - Hầu hết các trợ lý AI hiện nay chuyển 100% câu lệnh vào LLM sinh văn bản trên Cloud. Với các tác vụ xác định có tính quy tắc cao (ghi chi tiêu, hoàn thành việc, xem số dư, tính toán trả nợ), cách làm này gây lãng phí tài nguyên:
     - **Độ trễ cao:** 1.500 ms – 4.000 ms, phá vỡ trải nghiệm đàm thoại giọng nói tức thì (Voice-First).
     - **Tốn chi phí Token:** Tiêu hao hàng trăm token chỉ để trích xuất 2 trường dữ liệu.
     - **Ảo giác số học (Hallucination):** LLM dễ cộng trừ nhầm số dư hoặc suy diễn ngày tháng sai lệch.
3. **Hiện tượng quá tải ngữ cảnh (Prompt Bloat & Tool Misfire):**
   - Nếu nhồi nhét toàn bộ Prompt và danh sách Tools của cả hai miền nghiệp vụ Quản lý Tài chính và Quản lý Công việc vào một mô hình duy nhất, kích thước Prompt sẽ phình to, tỷ lệ chọn nhầm công cụ (Tool Misfire) tăng cao và thời gian phản hồi vượt SLA 3 giây.

**Mục đích kiến trúc (Intent):**
Lấy cảm hứng từ lý thuyết nhận thức hai hệ thống của Daniel Kahneman (*Thinking, Fast and Slow*), OnisAgent xây dựng kiến trúc **Dual-Path Cognitive Architecture**:
- **System 1 (Nhanh - Fast Path):** Đóng vai trò phản xạ bản năng tức thì thông qua mô hình quyết định chuyên biệt **Kev Decision Model** (`/v1/systemone`) thực thi các công cụ xác định (Python `Decimal` trên AWS Lambda) trong **~5–12 ms**, **0 Token LLM**.
- **System 2 (Chậm - Reasoning Path):** Đóng vai trò tư duy chiến lược, phân tích xu hướng dòng tiền sâu, dự toán khoản vay phức tạp và lập kế hoạch ngày/tuần thông qua **LLM (Amazon Bedrock / Ollama Cục bộ)**.
- **Multi-Agent Swarm (Strands Agents SDK):** Phân chia rõ ràng trách nhiệm chuyên môn giữa 3 Sub-Agents khi chạy trên luồng suy luận để tối ưu hóa context window và ngăn ngừa xung đột công cụ.

```
┌────────────────────────────────────────────────────────────────────────┐
│                      ĐẦU VÀO: GIỌNG NÓI / VĂN BẢN                      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                  [ 🧭 DECISION ROUTER & POLICY ENGINE ]
                                    │
            ┌───────────────────────┴───────────────────────┐
            ▼                                               ▼
  ⚡ SYSTEM 1: FAST PATH                        🧠 SYSTEM 2: REASONING PATH
  (Phản xạ tức thì · ~85% tác vụ)               (Suy luận sâu · ~15% tác vụ)
  • Mô hình: Kev Decision Model                 • Mô hình: Bedrock / Ollama LLM
  • Độ trễ: ~5 – 12 ms                          • Độ trễ: ~300 – 800 ms
  • Chi phí: 0 Token LLM                        • Triệt tiêu ảo giác: Grounded DB
  • Tác vụ: Ghi thu chi, tạo/xong task,         • Tác vụ: Phân tích xu hướng dòng tiền,
    xem số dư                                      dự toán khoản vay, lập kế hoạch ngày/tuần
            │                                               │
            │                                 [ 🐝 STRANDS MULTI-AGENT SWARM ]
            │                                 ├── CategorizationAgent
            │                                 ├── FinancialAdvisoryAgent
            │                                 └── TaskManagerAgent
            │                                               │
            └───────────────────────┬───────────────────────┘
                                    ▼
                      [ 💾 DATA LAYER / SỔ CÁI TẬP TRUNG ]
                      (DynamoDB + S3 Hybrid / onis_db.json)
```

---

### 2. Định Nghĩa Kỹ Thuật: Cơ Chế Decision Router & Policy Engine

#### 2.1. Thuật Toán Điều Phối Nhận Thức (Cognitive Routing Algorithm)
Cơ chế **Decision Router** phân luồng câu thoại và văn bản đầu vào:
Điểm vào của hệ thống tiếp nhận payload `{ state: "<user_input>" }` và phân loại theo công thức điều phối toán học:

$$\text{Path} = \begin{cases} 
\text{Blocked (Cảnh báo đỏ / Chặn)} & \text{nếu } \text{Risk} = \text{'write\_high'} \\
\text{Fast Path (System 1)} & \text{nếu } \text{Complexity} = \text{'simple'} \land \text{Confidence} \ge 0.65 \\
\text{Reasoning Path (System 2)} & \text{trong các trường hợp còn lại (phức tạp / mơ hồ)}
\end{cases}$$

#### 2.2. Fast Path (System 1 / Kev Decision Model)
- **Chuẩn giao tiếp TypeSafe `/v1/systemone`:** Dựa trên kiến trúc mô hình quyết định Kev, mô hình chuyên biệt phân loại ý định và độ phức tạp trước khi sinh bất kỳ từ ngữ nào.
- **Bộ nhãn ý định cốt lõi:**
  - *Tài chính:* `transaction.create_expense`, `transaction.create_income`, `transaction.query`, `finance.summary`.
  - *Công việc:* `task.create`, `task.complete`, `task.delete`, `task.query`.
  - *Suy luận:* `finance.analyze_spending`, `finance.loan_estimate`, `work.plan_day`, lập kế hoạch quỹ tiết kiệm và lời nhắc.
- **Hiệu chuẩn xác suất Softmax Calibrated ($T = 2.35$):**
  $$P(y_i) = \frac{e^{z_i / T}}{\sum_j e^{z_j / T}} \quad \text{với } T = 2.35$$
  Hệ số làm mềm $T=2.35$ ngăn ngừa tình trạng mô hình tự tin thái quá (overconfidence), bảo đảm chỉ những tác vụ thực sự rõ ràng ($\text{Confidence} \ge 0.65$) mới được thực thi tự động trên Fast Path.
- **Hiệu năng:** Xử lý trong **~5–12 ms**, **0 Token LLM**, tiết kiệm hơn 85% chi phí vận hành AI.

#### 2.3. Reasoning Path (System 2 / Amazon Bedrock / Ollama LLM)
- **Kích hoạt:** Khi yêu cầu thuộc nhóm suy luận chiến lược (`finance.analyze_spending`, `finance.loan_estimate`, `work.plan_day`), cần lập kế hoạch quỹ tiết kiệm/lời nhắc, khi độ phức tạp được đánh dấu `complex`, hoặc khi điểm tin cậy $< 0.65$.
- **Cơ chế Grounded Context Injection (Triệt tiêu 100% ảo giác số liệu):**
  LLM không bao giờ được tự bịa số liệu. Trước khi gọi LLM sinh văn bản, Decision Router tự động truy xuất snapshot dữ liệu thực tế từ DB và bơm vào prompt:
  ```json
  {
    "finance_summary": { "balance": 12631880, "total_expense": 2618120, "loan_installments": 4395794 },
    "recent_transactions": [ ... 8 giao dịch gần nhất ... ],
    "active_tasks": [ ... danh sách việc cần làm ... ]
  }
  ```
  LLM chỉ đóng vai trò phân tích xu hướng dòng tiền sâu và lập kế hoạch dựa trên dữ liệu thực tế này. Lịch trả góp khoản vay được tính bằng calculator Python `Decimal` trên AWS Lambda; LLM chỉ được diễn giải kết quả đó.
- **Dynamic Model Discovery:** Hệ thống hỗ trợ Amazon Bedrock trên Cloud và tự động phát hiện model cục bộ qua Ollama (`http://localhost:11434/api/tags`), ví dụ: `qwen2.5:3b` (tối ưu tiếng Việt), `gemma3:latest`, `qwen2.5-coder:14b`.

#### 2.4. Tầng Phòng Thủ Zero-Trust Policy Engine
Mọi đầu vào trước khi thực thi đều phải qua Policy Engine:
- `validate_transaction(amount, category, description)`: Chặn số tiền $\le 0$ hoặc vượt hạn mức an toàn (> 1 tỷ VNĐ/lần), chuẩn hóa tên danh mục.
- `validate_task(title)`: Làm sạch từ đệm, loại bỏ ký tự rác.
- Gắn nhãn `Risk = 'write_high'` với các thao tác nguy hiểm (xóa hàng loạt, sửa số dư ban đầu) để kích hoạt Human-in-the-Loop theo ADR-0004.

---

### 3. Phân Định Rạch Ròi 3 Sub-Agents Trong Strands Agents SDK

Khi luồng Reasoning Path cần phối hợp đa kỹ năng, **Strands Agents SDK** điều phối Swarm gồm 3 Sub-Agents với ranh giới chuyên môn độc lập:

| Tên Sub-Agent | Phạm Vi Trách Nhiệm Chuyên Biệt | Công Cụ Nghiệp Vụ (Tools) Được Cấp Quyền | Cam Kết Context & Prompt |
|---|---|---|---|
| **`CategorizationAgent`** | • Đọc và phân loại tự động thu/chi từ câu thoại tiếng Việt hoặc ảnh chụp hóa đơn (OCR/Text).<br>• Tự động khớp danh mục chuẩn và gán nhãn ngữ cảnh.<br>• Kiểm tra tính hợp lệ và trùng lặp của giao dịch. | • `extract_invoice_text`<br>• `match_category`<br>• `validate_transaction_rule` | Prompt tinh gọn chuyên sâu về phân loại ngôn ngữ tự nhiên tiếng Việt và hóa đơn; không chứa prompt tư vấn tài chính hay quản lý task. |
| **`FinancialAdvisoryAgent`** | • Phân tích xu hướng dòng tiền sâu và thói quen tiêu dùng cá nhân.<br>• Tư vấn lập kế hoạch nạp Quỹ Tiết kiệm và Lời nhắc thông minh.<br>• Hỗ trợ phân tích kịch bản vay trả góp dư nợ giảm dần. | • `calculate_balance`<br>• `calculate_expense_ratio`<br>• `calculate_loan_amortization`<br>• `get_savings_progress` | **Tuân thủ ADR-0001:** Bắt buộc gọi hàm Python `Decimal` để lấy số liệu trước khi sinh narration; tuyệt đối không tự tính toán số học. |
| **`TaskManagerAgent`** | • Quản lý danh sách nhiệm vụ, thời hạn (deadlines) và trạng thái công việc.<br>• Xây dựng **Ma trận Ưu tiên Động** (Dynamic Priority Matrix) dựa trên hạn chót và ngân sách thời gian.<br>• Tối ưu hóa lịch trình công việc trong ngày và trong tuần. | • `create_task`<br>• `update_task_status`<br>• `prioritize_matrix`<br>• `schedule_day_plan` | Quản lý độc lập miền công việc và năng suất cá nhân; không truy cập trái phép vào sổ cái giao dịch tài chính. |

**Cơ chế Giao tiếp & Handoff:**
- Các Sub-Agents trao đổi thông tin thông qua chuẩn JSON schema nghiêm ngặt trên nền tảng Strands SDK.
- Giới hạn tối đa số lần chuyển tiếp (Handoff limit = 3) để ngăn chặn vòng lặp vô hạn và kiểm soát chặt chẽ ngân sách token.
- Giảm hơn 40% dung lượng Prompt Token so với mô hình gom chung tất cả nghiệp vụ vào một Agent đơn khối.

---

### 4. Options Considered & Rejection Reasons (Các phương án & Lý do bác bỏ)

| Phương án | Ưu điểm (Pros) | Nhược điểm (Cons) | Lý do bác bỏ / lựa chọn |
|---|---|---|---|
| **Option A: Single Monolithic LLM (Một LLM xử lý 100% việc)** | Dễ lập trình giai đoạn đầu; không cần logic định tuyến hay phân chia agent. | Chậm (1.500–4.000 ms); tốn kém token (LLM Overkill); nguy cơ ảo giác số học; Prompt phình to gây Tool Misfire. | **BÁC BỎ:** Đi ngược lại hoàn toàn tiêu chí Voice-First và độ chính xác tài chính 100% của OnisAgent. |
| **Option B: LangChain / CrewAI Framework** | Cộng đồng lớn, nhiều tính năng dựng sẵn. | Quá nhiều tầng trừu tượng (overhead); khó đóng gói serverless; độ trễ cao; khó tích hợp mượt với mô hình quyết định Kev và AWS Bedrock AgentCore. | **BÁC BỎ:** Tăng độ phức tạp vận hành mà không mang lại ưu thế vượt trội về hiệu năng so với giải pháp chuyên biệt. |
| **Option C: Single-Agent Dual-Path Architecture + Strands Agents SDK Swarm** | Phản xạ tức thì 5–12 ms cho 85% tác vụ; 0 token LLM; triệt tiêu ảo giác bằng Grounded Context; tách bạch rõ ràng 3 Sub-Agents khi suy luận sâu. | Cần cài đặt và duy trì Decision Router, bộ hiệu chuẩn Softmax và cơ chế đồng bộ trạng thái giữa các agent. | **ĐƯỢC CHỌN:** Đáp ứng hoàn hảo các tiêu chuẩn đề ra trong Đề cương chi tiết: tốc độ siêu tốc, chi phí tối thiểu, độ tin cậy tuyệt đối. |

---

### 5. Directives & Rules (Quy định bắt buộc)

- **MUST (Cổng điều phối duy nhất):** Mọi tương tác từ người dùng (giọng nói hoặc văn bản) MUST đi qua `Decision Router & Policy Engine` làm điểm tiếp nhận đầu tiên.
- **MUST (Ngưỡng kích hoạt Fast Path):** Fast Path (System 1) chỉ được phép tự động thực thi khi thỏa mãn đồng thời:
  1. Ý định thuộc danh mục tác vụ nghiệp vụ xác định của Kev Model.
  2. Độ phức tạp là `simple`.
  3. Điểm tin cậy Softmax Calibrated ($T=2.35$) đạt $\text{Confidence} \ge 0.65$.
  4. Vượt qua toàn bộ quy tắc kiểm tra hợp lệ của Policy Engine.
- **MUST NOT (Cấm gọi LLM trên Fast Path):** Fast Path MUST NOT phát sinh bất kỳ lời gọi API nào tới LLM (Amazon Bedrock hoặc Ollama). Mọi kết quả phải được xử lý bằng logic nghiệp vụ và tool Python thuần `Decimal` trên AWS Lambda.
- **MUST (Grounded Context trên Reasoning Path):** Khi định tuyến vào Reasoning Path (System 2), hệ thống MUST tự động truy vấn dữ liệu thực tế từ CSDL để đưa vào Prompt ngữ cảnh trước khi sinh văn bản. Không được để LLM tự phỏng đoán số dư hay lịch sử giao dịch.
- **MUST (Tuân thủ ADR-0001):** Cả 3 Sub-Agents trên luồng Swarm (`CategorizationAgent`, `FinancialAdvisoryAgent`, `TaskManagerAgent`) MUST gọi hàm Python `Decimal` cho mọi phép tính số học trước khi diễn giải bằng văn bản.
- **MUST NOT (Cách ly Prompt & Tools):** Tuyệt đối không nhúng tools hoặc prompts của miền Quản lý Công việc vào miền Quản lý Tài chính và ngược lại.
- **ALWAYS (Chặn thao tác rủi ro cao):** Khi phát hiện hành vi có mức rủi ro `write_high`, Decision Router MUST chặn thực thi tự động và chuyển sang quy trình phê duyệt Human-in-the-Loop theo ADR-0004.

---

### 6. Consequences & Acceptance Criteria (Hệ quả & Tiêu chuẩn nghiệm thu)

#### A. Lợi ích đạt được
- **Đột phá về tốc độ:** Giảm hơn 95% độ trễ cho 85% tác vụ hàng ngày (~5–12 ms), mang lại trải nghiệm tương tác giọng nói tức thì.
- **Tối ưu chi phí Token:** Tiết kiệm khoảng 80–85% lượng token tiêu thụ so với mô hình trợ lý thuần LLM.
- **Triệt tiêu ảo giác số học:** Đạt độ chính xác 100% nhờ tách biệt tính toán bằng Python Decimal và kỹ thuật Grounded Context Injection.
- **Kiến trúc mô-đun hóa cao:** Dễ dàng bảo trì, nâng cấp độc lập từng Sub-Agent mà không ảnh hưởng đến toàn bộ hệ thống.

#### B. Đánh đổi & Thách thức
- Cần duy trì và giám sát độ chính xác của mô hình phân loại Kev System 1 (`/v1/systemone`).
- Đòi hỏi thiết lập cơ chế quản lý trạng thái phiên hội thoại (Session State) chặt chẽ giữa các Sub-Agents trên Strands SDK.

#### C. Tiêu chuẩn nghiệm thu (Acceptance Criteria)
1. **Tỷ lệ định tuyến Fast Path:** Đạt ít nhất $80 - 85\%$ tổng số yêu cầu mẫu hàng ngày được định tuyến thành công vào Fast Path.
2. **Độ trễ phản hồi:** Fast Path đạt thời gian xử lý trung bình trong khoảng **5 – 12 ms**; Reasoning Path phản hồi trong vòng **300 – 800 ms** (với local model) và không vượt quá SLA 3 giây trên Cloud.
3. **Mức tiêu thụ Token:** Xác minh bằng telemetry log ghi nhận **đúng 0 Token LLM** cho mọi tác vụ được xử lý trên Fast Path.
4. **Độ chính xác phân loại & chọn Tool:** Đạt tỷ lệ phân loại intent $\ge 90\%$ và độ chính xác chọn tool của các Sub-Agents $\ge 90\%$.
5. **Cách ly ngữ cảnh:** Kiểm thử Unit Test chứng minh 3 Sub-Agents hoạt động với Schema I/O độc lập và giảm $\ge 40\%$ Prompt Token so với prompt hợp nhất.

---

### 7. Revisit Triggers (Điều kiện xem xét lại)

Cần đánh giá lại quyết định kiến trúc này nếu:
1. Tỷ lệ phân loại nhầm ý định của System 1 vượt quá $10\%$ trên tập kiểm thử thực tế.
2. Thời gian phản hồi trung bình của Fast Path vượt quá 25 ms.
3. AWS ra mắt dịch vụ điều phối AI Agent thế hệ mới thay thế toàn diện Strands Agents SDK với chi phí và độ trễ thấp hơn rõ rệt.
4. Số lượng Sub-Agents tăng vượt quá 7 agents, đòi hỏi chuyển đổi sang mô hình Hierarchical Multi-Agent Orchestration.

---

Nhận xét cuối cùng: Kiến trúc Single-Agent Dual-Path kết hợp Multi-Agent Swarm là sự kết hợp hài hòa giữa "phản xạ tức thì" của Small Decision Model và "chiều sâu trí tuệ" của Large Language Model. Đây là chìa khóa giúp OnisAgent vượt qua mọi rào cản về độ trễ, chi phí và độ tin cậy để trở thành trợ lý cá nhân xuất sắc.
