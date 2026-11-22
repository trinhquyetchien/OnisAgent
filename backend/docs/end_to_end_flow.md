# OnisAgent – Đặc Tả Kiến Trúc & Luồng Hoạt Động End-to-End (End-to-End Architecture & Use-Case Flows)

> **Tài liệu đặc tả toàn diện luồng hoạt động từ đầu đến cuối cho hệ sinh thái OnisAgent**  
> Kết nối đồng bộ giữa **Flutter Web/Mobile Client**, **FastAPI Server**, **Mô hình Kev Decision Router (Fast Path)**, **Hệ thống Kiểm thử Slot & Phiên đa lượt (Clarification Engine)**, **Ollama Local LLM (Reasoning Path)** và **Tầng tính toán chính xác 100% Decimal**.  
> Tuân thủ các nguyên tắc thiết kế: [ADR-0001 (Decimal Money)](file:///home/trinhquyetchien/Projects/Main/Team/OnisAgent/docs/adr/ADR-0001-decimal-money-calculation.md), [ADR-0004 (HITL Safety Gate)](file:///home/trinhquyetchien/Projects/Main/Team/OnisAgent/docs/adr/ADR-0004-human-in-the-loop-workflow.md), [ADR-0006 (Domain Split & Clarification)](file:///home/trinhquyetchien/Projects/Main/Team/OnisAgent/docs/adr/ADR-0006-domain-split-intent-slot-clarification.md).

---

## 📑 Mục Lục
1. [Tổng Quan Kiến Trúc 5 Tầng End-to-End](#1-tổng-quan-kiến-trúc-5-tầng-end-to-end)
2. [Đặc Tả Chi Tiết 6 Kịch Bản Luồng Hoạt Động Cốt Lõi](#2-đặc-tả-chi-tiết-6-kịch-bản-luồng-hoạt-động-cốt-lõi)
   - [Trường hợp 1: Fast Path Hoàn Chỉnh (Thực thi tức thì ~6–10ms)](#trường-hợp-1-fast-path-hoàn-chỉnh-thực-thi-tức-thì-610ms)
   - [Trường hợp 2: Hội Thoại Làm Rõ Đa Lượt (Multi-turn Clarification Flow)](#trường-hợp-2-hội-thoại-làm-rõ-đa-lượt-multi-turn-clarification-flow)
   - [Trường hợp 3: Chốt An Toàn Human-in-the-Loop (HITL Safety Gate)](#trường-hợp-3-chốt-an-toàn-human-in-the-loop-hitl-safety-gate)
   - [Trường hợp 4: Reasoning Path (Phân tích chuyên sâu qua Ollama Local LLM)](#trường-hợp-4-reasoning-path-phân-tích-chuyên-sâu-qua-ollama-local-llm)
   - [Trường hợp 5: Giao Thoa Tiền & Việc (Cross-Domain - Dự định gắn kèm ngân sách)](#trường-hợp-5-giao-thoa-tiền--việc-cross-domain---dự-định-gắn-kèm-ngân-sách)
   - [Trường hợp 6: Xử Lý Ngoại Lệ & Dự Phòng (Fallback & Graceful Recovery)](#trường-hợp-6-xử-lý-ngoại-lệ--dự-phòng-fallback--graceful-recovery)
3. [Đặc Tả Giao Thức Dữ Liệu JSON (API Contract & State Machine)](#3-đặc-tả-giao-thức-dữ-liệu-json-api-contract--state-machine)
4. [Bảng Ma Trận Phân Phối Trách Nhiệm Giữa Các Tầng (Component Matrix)](#4-bảng-ma-trận-phân-phối-trách-nhiệm-giữa-các-tầng-component-matrix)

---

## 1. Tổng Quan Kiến Trúc 5 Tầng End-to-End

Hệ sinh thái OnisAgent kết hợp giữa **phản xạ vô điều kiện (System 1 - Fast Path)** với độ trễ < 10ms và **tư duy suy luận sâu (System 2 - Reasoning Path)** phục vụ phân tích tài chính và kế hoạch cuộc sống:

```mermaid
flowchart TD
    %% TẦNG 1: ĐẦU VÀO ĐA PHƯƠNG THỨC
    subgraph Tier1 ["📱 TẦNG 1: MULTI-MODAL CLIENT TIER (FLUTTER WEB / MOBILE)"]
        VoiceIn["🎤 Voice Input (Push-To-Talk / Web Speech API)"]
        TextIn["💬 Text Input (Chat Bar / Action Chips)"]
        VoiceIn --> STTPipeline["Speech-To-Text Processor"]
        STTPipeline --> ClientPayload["Client HTTP/REST Payload: {session_id, user_id, text}"]
        TextIn --> ClientPayload
    end

    %% TẦNG 2: ĐỊNH TUYẾN NHẬN THỨC
    subgraph Tier2 ["⚡ TẦNG 2: COGNITIVE ROUTER & KEV INFERENCE (~6ms · 0 TOKEN)"]
        ClientPayload --> FastAPIServer["FastAPI Gateway (/api/v1/chat)"]
        FastAPIServer --> KevClassifier["⚡ Kev Intent Pipeline<br>(Dual-layer TF-IDF + Calibrated LinearSVC)"]
        KevClassifier --> RouteDecision{"Định tuyến lộ trình<br>(Intent Type & Confidence >= 0.50)"}
    end

    %% TẦNG 3: QUẢN LÝ PHIÊN & KIỂM ĐỊNH SLOT
    subgraph Tier3 ["🛡️ TẦNG 3: DOMAIN SPLIT & MULTI-TURN CLARIFICATION ENGINE"]
        RouteDecision -->|Routine Intent / High Conf| FastPathBranch["Tuyến Fast Path (System 1)"]
        RouteDecision -->|Complex / Low Conf| ReasoningBranch["Tuyến Reasoning Path (System 2)"]

        FastPathBranch --> SlotExtractor["Bộ trích xuất Slot tự nhiên (Regex & Heuristics)"]
        SlotExtractor --> SessionMgr["🔄 Multi-turn SessionManager (In-memory)"]
        SessionMgr --> SlotVal["🛡️ SlotValidator (Pydantic V2 Schemas)"]
        
        SlotVal --> SlotCheck{"Kiểm tra Slots bắt buộc?"}
        SlotCheck -->|Thiếu Slot| ClarifyState["❓ Trạng thái: NEED_CLARIFICATION<br>+ Câu hỏi làm rõ & Action Chips"]
        SlotCheck -->|Hành động nhạy cảm| HitlState["🛑 Trạng thái: BLOCKED (HITL Gate)<br>+ Yêu cầu User xác nhận xóa/áp dụng"]
        SlotCheck -->|Đủ Slots| ReadyState["✅ Trạng thái: READY"]
    end

    %% TẦNG 4: THỰC THI & SUY LUẬN
    subgraph Tier4 ["⚙️ TẦNG 4: COMPUTE & REASONING ENGINES"]
        ReadyState --> ActionExecutor["🚀 Deterministic Fast-Path Action Executor"]
        ActionExecutor --> Templates["📝 response_templates.py (Văn phong chuẩn)"]
        ActionExecutor --> DecimalCalc["🧮 100% Exact Python Decimal Calculator"]

        ReasoningBranch --> GroundingContext["Context Grounder (Số dư, thu chi, sổ nợ, task)"]
        GroundingContext --> OllamaLocal["🧠 Local Ollama LLM (Qwen2.5:3b @ 127.0.0.1:11434)<br><i>100% Free · Chạy offline trực tiếp trên máy</i>"]
    end

    %% TẦNG 5: LƯU TRỮ VÀ PHẢN HỒI
    subgraph Tier5 ["💾 TẦNG 5: PERSISTENCE & UNIFIED RESPONSE"]
        DecimalCalc --> LocalStore[("Local SQLite / DynamoDB Client")]
        Templates --> UnifiedResponse["JSON ChatResponse: {session_id, intent, status, message, quick_replies, data}"]
        OllamaLocal --> UnifiedResponse
        ClarifyState --> UnifiedResponse
        HitlState --> UnifiedResponse
        UnifiedResponse --> FlutterUI["📱 Flutter UI Render: Tin nhắn Chat + Quick-Reply Chips"]
    end
```

---

## 2. Đặc Tả Chi Tiết 6 Kịch Bản Luồng Hoạt Động Cốt Lõi

---

### Trường hợp 1: Fast Path Hoàn Chỉnh (Thực thi tức thì ~6–10ms)
* **Ý nghĩa:** Người dùng ra lệnh cho các tác vụ thường nhật đầy đủ thông số (chi tiêu, kiểm tra số dư, danh sách công việc hôm nay, tra cứu sổ nợ).
* **Mẫu câu thực tế:** *"chi 45k trà sữa"*, *"ví momo còn bao nhiêu"*, *"hôm nay có việc gì cần làm"*, *"tôi có nợ ai không"*.

```mermaid
sequenceDiagram
    autonumber
    actor User as Người dùng (Voice / Text)
    participant UI as Flutter App (Web/Mobile)
    participant API as FastAPI Server (/api/v1/chat)
    participant Kev as Kev Decision Router (~6ms)
    participant Val as SlotValidator & SessionManager
    participant Tool as Decimal Calculator / Storage
    participant Res as Response Template Engine

    User->>UI: "chi 45k trà sữa hôm nay"
    UI->>API: POST /api/v1/chat {text: "chi 45k trà sữa hôm nay", session_id: "s1"}
    API->>Kev: predict_proba(["chi 45k trà sữa hôm nay"])
    Kev-->>API: Intent: finance.add_expense (Conf: 0.98), Route: FAST_PATH
    API->>Val: parse_slots_from_text() -> {amount: 45000, note: "trà sữa"}
    Val->>Val: ExpenseCreateSlot validation (Thỏa mãn amount & note)
    Val-->>API: ActionResponse (Status: READY, Domain: FINANCE)
    API->>Tool: Ghi sổ quỹ chi tiêu chính xác với Decimal("45000")
    Tool-->>API: Updated Transaction Record
    API->>Res: execute_fast_path_action("finance.add_expense", slots)
    Res-->>API: (Message: "Đã ghi nhận khoản chi 45.000₫ cho 'trà sữa'", Chips: ["Xem số dư", "Lịch sử chi tiêu"])
    API-->>UI: 200 OK ChatResponse (Status: READY, Latency: 7.2ms)
    UI-->>User: Hiển thị bong bóng chat xác nhận kèm Action Chips
```

---

### Trường hợp 2: Hội Thoại Làm Rõ Đa Lượt (Multi-turn Clarification Flow)
* **Ý nghĩa:** Người dùng chỉ nói câu chung chung hoặc thiếu tham số bắt buộc. Hệ thống duy trì phiên (Session), hỏi lại tự nhiên kèm các nút gợi ý bấm nhanh (Quick-Reply Chips), sau đó tự động ghép nối (merge) tham số ở lượt tiếp theo.
* **Mẫu câu thực tế:**  
  * Lượt 1: *"Vừa đi ăn phở bò"* (Thiếu số tiền `amount`).  
  * Lượt 2: Bấm nút `"50.000₫"` hoặc nói *"50k"*.

```mermaid
sequenceDiagram
    autonumber
    actor User as Người dùng
    participant UI as Flutter App
    participant API as FastAPI Server
    participant Kev as Kev Classifier
    participant Session as SessionManager (Multi-turn)
    participant Val as SlotValidator

    %% LƯỢT 1
    Note over User,Val: === LƯỢT HỘI THOẠI 1 (THIẾU THÔNG TIN) ===
    User->>UI: "Vừa đi ăn phở bò"
    UI->>API: POST /api/v1/chat {text: "Vừa đi ăn phở bò", session_id: "sess_42"}
    API->>Kev: Phân loại -> finance.add_expense (Conf: 0.96)
    API->>Session: process_turn(session_id="sess_42", intent="finance.add_expense", slots={note: "ăn phở bò", category: "Ăn uống"})
    Session->>Val: Validate slots -> Thiếu 'amount'
    Val-->>Session: ActionResponse (Status: NEED_CLARIFICATION, missing_slot: "amount")
    Session->>Session: Lưu session state: waiting_for_slot = "amount", accumulated_slots = {note, category}
    Session-->>API: NEED_CLARIFICATION payload
    API-->>UI: ChatResponse (Status: NEED_CLARIFICATION, Message: "Bạn đã chi bao nhiêu tiền cho 'ăn phở bò' vậy?", QuickReplies: ["30.000₫", "45.000₫", "50.000₫", "100.000₫"])
    UI-->>User: Hiển thị câu hỏi làm rõ + dãy Action Chips dạng nút bấm

    %% LƯỢT 2
    Note over User,Val: === LƯỢT HỘI THOẠI 2 (BỔ SUNG THAM SỐ) ===
    User->>UI: Bấm chip "50.000₫" (hoặc nói "50k")
    UI->>API: POST /api/v1/chat {text: "50k", session_id: "sess_42"}
    API->>Session: Kiểm tra: session "sess_42" đang waiting_for_slot = "amount"
    Session->>Session: Merge slot: accumulated_slots + {amount: Decimal("50000")}
    Session->>Val: Validate slots đã merge -> ĐỦ 100% BẮT BUỘC
    Val-->>Session: ActionResponse (Status: READY)
    Session->>Session: Reset waiting_for_slot = None, clear accumulated_slots
    Session-->>API: READY
    API-->>UI: ChatResponse (Status: READY, Message: "Đã ghi nhận khoản chi 50.000₫ cho 'ăn phở bò' (Nguồn: default_account).")
    UI-->>User: Cập nhật giao diện hoàn tất giao dịch
```

---

### Trường hợp 3: Chốt An Toàn Human-in-the-Loop (HITL Safety Gate)
* **Ý nghĩa:** Áp dụng cho các hành vi rủi ro cao gây mất mát dữ liệu hoặc cam kết tài chính lớn ([ADR-0004](file:///home/trinhquyetchien/Projects/Main/Team/OnisAgent/docs/adr/ADR-0004-human-in-the-loop-workflow.md)): Xóa công việc vĩnh viễn (`task.delete`), khởi tạo gói vay lớn (`finance.loan_installment_plan`).
* **Mẫu câu thực tế:** *"Xóa vĩnh viễn task làm slide thuyết trình"*.

```mermaid
sequenceDiagram
    autonumber
    actor User as Người dùng
    participant UI as Flutter App
    participant API as FastAPI Server
    participant Val as SlotValidator (HITL Gate 3)
    participant DB as SQLite / DynamoDB Storage

    User->>UI: "Xóa task làm slide thuyết trình"
    UI->>API: POST /api/v1/chat {text: "Xóa task làm slide thuyết trình"}
    API->>Val: validate("task.delete", {title: "làm slide thuyết trình"})
    Val->>Val: Phát hiện hành vi nguy hiểm (DESTRUCTIVE_ACTION)
    Val-->>API: ActionResponse (Status: BLOCKED, requires_hitl: True, Message: "Xác nhận xóa công việc 'làm slide thuyết trình'?")
    API-->>UI: ChatResponse (Status: BLOCKED, requires_hitl: True, quick_replies: ["Xác nhận", "Hủy bỏ"])
    UI-->>User: Hiện cảnh báo màu cam đỏ & Yêu cầu nhấn xác nhận (Modal Dialog)
    
    alt Người dùng nhấn [Xác nhận]
        User->>UI: Nhấn "Xác nhận"
        UI->>API: POST /api/v1/chat {text: "Xác nhận", session_id: "...", slots: {confirmed: true}}
        API->>DB: Thực hiện xóa vĩnh viễn bản ghi task trong DB
        DB-->>API: OK (Rows affected: 1)
        API-->>UI: ChatResponse (Status: READY, Message: "Đã xóa thành công công việc 'làm slide thuyết trình'.")
        UI-->>User: Thông báo đã xóa
    else Người dùng nhấn [Hủy bỏ]
        User->>UI: Nhấn "Hủy bỏ"
        UI->>API: POST /api/v1/chat {text: "Hủy bỏ"}
        API-->>UI: ChatResponse (Status: READY, Message: "Đã hủy thao tác xóa. Công việc được giữ nguyên an toàn.")
        UI-->>User: Giữ nguyên trạng thái cũ
    end
```

---

### Trường hợp 4: Reasoning Path (Phân tích chuyên sâu qua Ollama Local LLM)
* **Ý nghĩa:** Giải quyết các câu hỏi tư vấn tài chính, báo cáo dòng tiền chuyên sâu hoặc lập lịch tối ưu ma trận Eisenhower.
* **Mô hình phụ trách:** **Ollama Local LLM (`qwen2.5:3b`)** chạy trực tiếp tại `http://127.0.0.1:11434` (100% miễn phí, bảo mật cục bộ, không gửi dữ liệu ra ngoài).
* **Mẫu câu thực tế:** *"Tôi muốn tiết kiệm 50 triệu trong 6 tháng, hãy phân tích thu chi hiện tại và tư vấn"*.

```mermaid
sequenceDiagram
    autonumber
    actor User as Người dùng
    participant UI as Flutter App
    participant API as FastAPI Server
    participant Kev as Kev Router (System 1)
    participant DB as Internal Data Layer (Context Grounding)
    participant Ollama as Ollama Local LLM (qwen2.5:3b)

    User->>UI: "Tôi muốn dành được 50 triệu trong 6 tháng, hãy phân tích thu chi hiện tại và đề xuất lộ trình"
    UI->>API: POST /api/v1/chat {text: "..."}
    API->>Kev: predict() -> Intent: finance.financial_report
    Kev-->>API: Nhận diện Intent phức tạp -> Phân luồng REASONING_PATH
    API->>DB: Truy vấn dữ liệu thực tế của User:
    Note over DB: • Số dư ví: 18.450.000₫<br>• Thu nhập trung bình: 20.000.000₫/tháng<br>• Chi tiêu trung bình: 11.000.000₫/tháng<br>• Dư nòng cốt: +9.000.000₫/tháng
    DB-->>API: Context JSON payload (Grounding Data)
    API->>Ollama: POST /api/chat {model: "qwen2.5:3b", messages: [SystemPrompt, UserPrompt + Context]}
    Note over Ollama: Qwen2.5 tính toán theo ngữ cảnh:<br>Mỗi tháng cần tiết kiệm 8.333.333₫<br>Thu 20tr - Chi 11tr = Dư 9tr<br>-> Khả thi cao! Đề xuất cắt giảm ăn ngoài 500k.
    Ollama-->>API: Báo cáo phân tích tiếng Việt sâu sắc, có cấu trúc bullet point
    API-->>UI: 200 OK (Route: REASONING_PATH, Status: READY, Message: <Lời khuyên Qwen>, QuickReplies: ["Đặt mục tiêu tiết kiệm", "Xem báo cáo chi tiết"])
    UI-->>User: Hiển thị bài tư vấn tài chính chuyên nghiệp từ AI
```

---

### Trường hợp 5: Giao Thoa Tiền & Việc (Cross-Domain - Dự định gắn kèm ngân sách)
* **Ý nghĩa:** Người dùng lên kế hoạch hành trình, du lịch, sự kiện đời sống gắn với số tiền ước tính. Hệ thống vừa chia ngân sách theo các hạng mục thực tế, vừa sinh checklist công việc cần chuẩn bị.
* **Mẫu câu thực tế:** *"Tính đi Đà Lạt 3 ngày dự chi khoảng 3 triệu"*, *"Kế hoạch đi phượt Hà Giang dự toán 2 củ"*.

```mermaid
sequenceDiagram
    autonumber
    actor User as Người dùng
    participant UI as Flutter App
    participant API as FastAPI Server
    participant Kev as Kev Intent Classifier
    participant Ollama as Ollama Local LLM (Travel/Budget Expert)
    participant System as System Data Sync

    User->>UI: "tính đi đà lạt 3 ngày dự chi khoảng 3 triệu"
    UI->>API: POST /api/v1/chat {text: "..."}
    API->>Kev: Phân loại -> cross.plan_expense_task (Conf: 0.94)
    Kev-->>API: Route: REASONING_PATH
    API->>Ollama: Kích hoạt System Prompt chuyên gia Lập hành trình & Phân bổ tài chính
    Note over Ollama: Phân bổ ngân sách 3.000.000₫:<br>• Xe di chuyển: 15% (450k)<br>• Khách sạn: 25% (750k)<br>• Ăn uống: 30% (900k)<br>• Vé tham quan: 15% (450k)<br>• Dự phòng: 15% (450k)<br>+ Packing List (Áo ấm, CMND, thuốc)
    Ollama-->>API: Kế hoạch chi tiết + Checklist
    API->>System: Tự động trích xuất các công việc chuẩn bị vào Task Queue
    API-->>UI: ChatResponse (Route: REASONING_PATH, Message: <Kế hoạch chi tiết>, QuickReplies: ["Lưu kế hoạch", "Tạo ngân sách", "Thêm việc cần chuẩn bị"])
    UI-->>User: Hiển thị giao diện kế hoạch du lịch & danh sách công việc cần làm
```

---

### Trường hợp 6: Xử Lý Ngoại Lệ & Dự Phòng (Fallback & Graceful Recovery)
* **Ý nghĩa:** Bảo đảm tính ổn định tuyệt đối (Zero Downtime / High Resilience) trong 2 tình huống sự cố:
  1. Người dùng nói câu không rõ nghĩa / nằm ngoài 33 Intent.
  2. Dịch vụ Ollama Local LLM chưa bật hoặc bị treo timeout.

```mermaid
sequenceDiagram
    autonumber
    actor User as Người dùng
    participant API as FastAPI Server
    participant Kev as Kev Classifier
    participant Ollama as Ollama Local LLM Client
    participant Fallback as Response Templates (Fallback Mode)

    alt TÌNH HUỐNG 6A: CÂU LỆNH NGOÀI PHẠM VI (CONFIDENCE < 0.40)
        User->>API: "Hôm nay trời có mưa ở sao hỏa không?"
        API->>Kev: Inference -> Top intent có confidence = 0.21 (< threshold)
        API->>Fallback: template_system_help()
        Fallback-->>API: Lời chào và gợi ý các mẫu câu lệnh thực tế mà OnisAgent hỗ trợ
        API-->>User: "Tôi là OnisAgent - Trợ lý hợp nhất Quản lý Tài chính & Công việc..." kèm Quick-Replies mẫu.
    else TÌNH HUỐNG 6B: OLLAMA LOCAL BỊ TẮT HOẶC TIMEOUT (>12s)
        User->>API: "Phân tích tài chính tháng này giúp tôi" (REASONING_PATH)
        API->>Ollama: Gửi request tới http://127.0.0.1:11434 (Connection Refused / Timeout)
        Note over Ollama: Ollama process không phản hồi
        Ollama->>Ollama: Bắt ngoại lệ httpx.ConnectError / TimeoutException
        Ollama->>Fallback: _generate_fallback(prompt, context)
        Fallback-->>Ollama: Bản phân tích dự phòng an toàn dựa trên số dư và cảnh báo dòng tiền
        Ollama-->>API: Fallback Response (Không làm crash API)
        API-->>User: 200 OK với phân tích dự phòng chuẩn mực (App vẫn chạy mượt mà 100%)
    end
```

---

## 3. Đặc Tả Giao Thức Dữ Liệu JSON (API Contract & State Machine)

### 3.1. Máy Trạng Thái Phiên Hội Thoại (Session State Machine)

```mermaid
stateDiagram-v2
    [*] --> READY: Phiên khởi tạo mới
    READY --> NEED_CLARIFICATION: Thiếu Slot bắt buộc (amount, title, category...)
    NEED_CLARIFICATION --> READY: Người dùng bổ sung đủ Slot qua Chat / Quick-Reply Chip
    NEED_CLARIFICATION --> READY: Người dùng chuyển hẳn sang chủ đề / Intent khác
    READY --> BLOCKED: Phát hiện hành động nhạy cảm (Xóa task, xóa quỹ - HITL Gate)
    BLOCKED --> EXECUTED: Người dùng chọn [Xác nhận] (User Approval)
    BLOCKED --> READY: Người dùng chọn [Hủy bỏ] (User Cancel)
    READY --> EXECUTED: Thực thi hoàn tất (Ghi sổ quỹ / Tạo task)
    EXECUTED --> READY: Sẵn sàng cho lượt lệnh tiếp theo
    READY --> FAILED: Lỗi xác thực dữ liệu (Pydantic ValidationError)
```

---

### 3.2. Bảng Ánh Xạ Request / Response Payload Chuẩn

#### 1. Yêu Cầu Gửi Tin Nhắn (`POST /api/v1/chat`):
```json
{
  "session_id": "sess_user_001_mobile",
  "user_id": "user_chiendn",
  "text": "chi 45k trà sữa hôm nay",
  "slots": {}
}
```

#### 2. Phản Hồi Thành Công Khi Đủ Thông Tin (`READY - Fast Path`):
```json
{
  "session_id": "sess_user_001_mobile",
  "intent": "finance.add_expense",
  "confidence": 0.9821,
  "route": "FAST_PATH",
  "status": "READY",
  "message": "Đã ghi nhận khoản chi 45.000₫ cho 'trà sữa' (Nguồn: default_account).",
  "reply": "Đã ghi nhận khoản chi 45.000₫ cho 'trà sữa' (Nguồn: default_account).",
  "quick_replies": ["Xem số dư", "Ghi thêm khoản chi", "Lịch sử chi tiêu"],
  "slots": {
    "amount": 45000.0,
    "category": "Ăn uống",
    "note": "chi 45k trà sữa hôm nay",
    "account": "default_account"
  },
  "data": {
    "transaction_type": "expense",
    "recorded": {
      "amount": 45000.0,
      "category": "Ăn uống",
      "note": "chi 45k trà sữa hôm nay"
    }
  },
  "requires_hitl": false,
  "latency_ms": 6.85
}
```

#### 3. Phản Hồi Khi Cần Làm Rõ (`NEED_CLARIFICATION`):
```json
{
  "session_id": "sess_user_001_mobile",
  "intent": "finance.add_expense",
  "confidence": 0.9612,
  "route": "FAST_PATH",
  "status": "NEED_CLARIFICATION",
  "message": "Bạn đã chi bao nhiêu tiền cho 'ăn phở bò' vậy?",
  "reply": "Bạn đã chi bao nhiêu tiền cho 'ăn phở bò' vậy?",
  "quick_replies": ["30.000₫", "45.000₫", "50.000₫", "100.000₫"],
  "slots": {
    "category": "Ăn uống",
    "note": "ăn phở bò"
  },
  "data": null,
  "requires_hitl": false,
  "latency_ms": 5.42
}
```

#### 4. Phản Hồi Khi Chặn Chờ Người Dùng Phê Duyệt (`BLOCKED - HITL Gate`):
```json
{
  "session_id": "sess_user_001_mobile",
  "intent": "task.delete",
  "confidence": 0.9854,
  "route": "FAST_PATH",
  "status": "BLOCKED",
  "message": "Hành động này cần bạn xác nhận trước khi thực hiện: Xác nhận xóa công việc 'báo cáo đồ án AI4Life'?",
  "reply": "Hành động này cần bạn xác nhận trước khi thực hiện: Xác nhận xóa công việc 'báo cáo đồ án AI4Life'?",
  "quick_replies": ["Xác nhận", "Hủy bỏ"],
  "slots": {
    "title": "báo cáo đồ án AI4Life"
  },
  "data": null,
  "requires_hitl": true,
  "latency_ms": 4.12
}
```

#### 5. Phản Hồi Từ Tầng Suy Luận Sâu (`REASONING_PATH - Ollama Local LLM`):
```json
{
  "session_id": "sess_user_001_mobile",
  "intent": "cross.plan_expense_task",
  "confidence": 0.9353,
  "route": "REASONING_PATH",
  "status": "READY",
  "message": "### Lập bảng phân bổ ngân sách du lịch Đà Lạt 3 ngày (Tổng: 3.000.000₫)\n• 🚗 Vé xe di chuyển: 450.000₫ (15%)\n• 🏨 Khách sạn lưu trú: 750.000₫ (25%)\n• 🍜 Ăn uống trải nghiệm: 900.000₫ (30%)\n• 🎟️ Vé tham quan hoạt động: 450.000₫ (15%)\n• 🛡️ Quỹ dự phòng phát sinh: 450.000₫ (15%)\n\n### Việc cần chuẩn bị (To-do list):\n1. Đặt vé xe Limousine trước 3 ngày.\n2. Chuẩn bị áo ấm, CMND/CCCD và thuốc say xe.",
  "reply": "...",
  "quick_replies": ["Lưu kế hoạch", "Tạo ngân sách", "Thêm việc cần chuẩn bị"],
  "slots": {
    "event_name": "đi đà lạt 3 ngày",
    "budget": 3000000.0
  },
  "data": {
    "provider": "ollama",
    "model": "qwen2.5:3b"
  },
  "requires_hitl": false,
  "latency_ms": 4820.15
}
```

---

## 4. Bảng Ma Trận Phân Phối Trách Nhiệm Giữa Các Tầng (Component Matrix)

| Thành phần / Tầng | Tệp tin thực thi chính | Trách nhiệm chính | Tiêu chuẩn tốc độ |
| :--- | :--- | :--- | :---: |
| **Client Gateway** | `app/lib/services/api_service.dart` | Giao tiếp REST API, quản lý WebSocket/Chat Stream, hiển thị Quick Replies | Trực quan, < 16ms render (60fps) |
| **API Gateway** | `backend/src/main.py` | FastAPI application, middleware CORS, điều phối Fast Path vs Reasoning Path | < 2ms routing overhead |
| **Kev Decision Router** | `backend/src/models/kev/` | TF-IDF n-grams + Calibrated LinearSVC phân loại 33 Intent tiếng Việt | **~5–10ms** |
| **Validation Engine** | `backend/src/engine/slot_validator.py` | Kiểm tra tính hợp lệ của Slot theo Pydantic V2, kích hoạt chốt duyệt an toàn HITL | < 1ms |
| **Session Manager** | `backend/src/engine/session_manager.py` | Quản lý bộ nhớ phiên đa lượt, gộp các slots thiếu giữa các turn | < 1ms |
| **Response Templates** | `backend/src/engine/response_templates.py` | Cung cấp mẫu câu trả lời chuẩn xác, sinh động kèm action chips theo intent | < 0.5ms |
| **Decimal Arithmetic** | `backend/src/tools/calculator.py` | Tính toán số dư, lãi suất vay, chia hóa đơn chính xác tuyệt đối không ảo giác | < 0.1ms |
| **Reasoning Path LLM** | `backend/src/agents/ollama_client.py` | Kết nối Ollama `qwen2.5:3b`, lập kế hoạch chi tiêu & thời gian, tự động fallback | ~3–7 giây (tùy độ dài) |

---

## 5. Kết Luận
Tài liệu này là **kim chỉ nam duy nhất** chuẩn hóa toàn bộ luồng dữ liệu, quy tắc chuyển trạng thái và trách nhiệm từng module trong OnisAgent Backend. Đảm bảo toàn bộ đội ngũ phát triển Frontend và Backend tích hợp hoàn hảo, không có điểm nghẽn và đạt trải nghiệm mượt mà nhất cho người dùng.
