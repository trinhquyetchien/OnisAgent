---
id: ADR-0003
timestamp: 2026-10-10T00:00:00Z
status: accepted
deciders: Trịnh Quyết Chiến, Hứa Huỳnh Anh
tags:
  - onisagent
  - aws
  - database
  - dynamodb
  - s3
  - hybrid-storage
  - serverless
  - no-sql
  - temp-audio
  - voice-first
  - local-sync
  - onis-db-json
related_adrs: [ADR-0001, ADR-0002, ADR-0004, ADR-0005]
---

# ADR-0003: DynamoDB Schema (Transactions, Tasks, Sessions, SavingsGoals) & S3 Blob Storage

> **Y-Statement:** Trong ngữ cảnh OnisAgent cần quản lý song song dữ liệu có cấu trúc tần suất cao (giao dịch thu/chi, nhiệm vụ công việc, mục tiêu tiết kiệm, bộ nhớ phiên và nhật ký telemetry) và dữ liệu phi cấu trúc (ảnh chụp hóa đơn, file đệm âm thanh giọng nói tạm thời Temp Audio), đồng thời hỗ trợ phát triển thử nghiệm/offline không cần AWS credentials, chúng tôi quyết định sử dụng **Amazon DynamoDB** làm CSDL NoSQL cốt lõi gồm 4 bảng chuyên biệt (`Transactions`, `Tasks`, `Sessions`, `SavingsGoals`), kết hợp **Amazon S3** làm Blob Storage lưu trữ hóa đơn và đệm âm thanh tạm thời (với Lifecycle Rule tự động dọn dẹp sau 24–48h), đồng thời thiết lập **Cơ chế Đồng bộ Cục bộ (Local Sync Fallback)** qua file `data/onis_db.json` và SQLite, chấp nhận sự đánh đổi về việc phải quản lý ánh xạ khóa tham chiếu (S3 Object Key) và duy trì lớp trừu tượng repository hai chế độ (Cloud vs Local).

---

### 1. Problem Statement & Architectural Intent (Bài toán & Ý tưởng Kiến trúc)

**Bài toán (Context):**
OnisAgent hoạt động trong môi trường đa nền tảng (Web Dashboard, Mobile App, Smartwatch) và xử lý 3 nhóm dữ liệu hoàn toàn khác biệt:
1. **Dữ liệu có cấu trúc thao tác tần suất cao (High-Frequency Structured Data):**
   - Thu chi cá nhân, hạn mức ngân sách, danh sách việc cần làm (tasks), tiến độ mục tiêu tiết kiệm, và bộ nhớ hội thoại của Agent.
   - Yêu cầu: Độ trễ truy vấn cực thấp (< 10 ms), khả năng mở rộng quy mô tức thì (Serverless), chi phí thanh toán theo dung lượng sử dụng thực tế (Pay-as-you-go), và cô lập dữ liệu tuyệt đối theo từng người dùng (`user_id`).
2. **Dữ liệu nhị phân & phương tiện kích thước lớn (Unstructured Blob & Audio Buffer):**
   - Ảnh chụp hóa đơn/biên lai mua sắm, tài liệu PDF sao kê ngân hàng phục vụ OCR.
   - File ghi âm giọng nói tiếng Việt tạm thời từ tính năng Speech-to-Text (STT) và các file âm thanh phản hồi Text-to-Speech (TTS) của giao diện Voice-First.
   - Vấn đề: DynamoDB giới hạn kích thước mỗi item tối đa là 400 KB. Việc nhúng dữ liệu nhị phân (Base64) vào NoSQL item là một anti-pattern nghiêm trọng, gây tiêu tốn RCU/WCU và làm nghẽn băng thông CSDL.
3. **Nhu cầu phát triển cục bộ và hoạt động ngoại tuyến (Local Dev & Offline Fallback):**
   - Các nhà phát triển cần môi trường chạy thử nghiệm độc lập trên máy cá nhân mà không phụ thuộc vào AWS credentials hay kết nối Internet liên tục.
   - Trải nghiệm trên thiết bị di động và đồng hồ thông minh đòi hỏi khả năng lưu trữ cục bộ tạm thời (Offline-First) trước khi đồng bộ lên máy chủ.

**Mục đích kiến trúc (Intent):**
Thiết lập kiến trúc lưu trữ lai phân tầng rõ ràng (Hybrid Tiered Storage Architecture):
- **Tầng CSDL NoSQL Cloud (Amazon DynamoDB):** Đảm nhiệm vai trò sổ cái dữ liệu có cấu trúc với 4 bảng được thiết kế chuẩn Single/Multi-table pattern.
- **Tầng Blob Storage (Amazon S3):** Lưu trữ đối tượng nhị phân lớn và đệm âm thanh tạm thời (Temp Audio Buffer) với chính sách tự động xóa sau 24–48 giờ.
- **Tầng Lưu trữ Cục bộ (Local Storage Fallback):** Hỗ trợ tệp JSON chuẩn hóa `data/onis_db.json` và SQLite, bảo đảm 100% tính năng hoạt động trơn tru trong môi trường offline/development.

---

### 2. Chi Tiết Hóa Data Schema trong DynamoDB & Amazon S3

#### 2.1. Cấu Trúc 4 Bảng CSDL Cốt Lõi Trên Amazon DynamoDB
Tất cả các bảng đều sử dụng `user_id` làm Partition Key (PK) để bảo đảm cô lập dữ liệu người dùng (Tenant Isolation) và tối ưu hóa hiệu năng truy vấn.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              AMAZON DYNAMODB SCHEMA                                    │
├───────────────────┬───────────────────┬────────────────────────────────────────────────┤
│ Bảng              │ Khóa chính (PK/SK)│ Thuộc tính nghiệp vụ cốt lõi                   │
├───────────────────┼───────────────────┼────────────────────────────────────────────────┤
│ 1. Transactions   │ PK: user_id       │ • amount (Decimal), category (String)          │
│                   │ SK: tx_{ts}_{id}  │ • description, type (expense/income), date     │
│                   │                   │ • path_source (fast_path_system1 | reasoning)  │
│                   │                   │ • s3_receipt_key (String / URL)                │
├───────────────────┼───────────────────┼────────────────────────────────────────────────┤
│ 2. Tasks          │ PK: user_id       │ • title (String), deadline (ISO-8601)          │
│                   │ SK: task_{ts}_{id}│ • priority (high | medium | low)               │
│                   │                   │ • status (pending | completed)                 │
│                   │                   │ • tags (List[String]), completed_at            │
├───────────────────┼───────────────────┼────────────────────────────────────────────────┤
│ 3. Sessions       │ PK: user_id       │ • chat_history (List[MessageObj])              │
│                   │ SK: sess_{sess_id}│ • agent_memory (Long-term rules, preferences)  │
│                   │                   │ • telemetry_logs (latency_ms, confidence,      │
│                   │                   │   token_saved, model_used)                     │
├───────────────────┼───────────────────┼────────────────────────────────────────────────┤
│ 4. SavingsGoals   │ PK: user_id       │ • goal_name (String), target_amount (Decimal)  │
│                   │ SK: goal_{goal_id}│ • current_amount (Decimal), deadline (ISO)     │
│                   │                   │ • progress_percentage (Decimal), status        │
└───────────────────┴───────────────────┴────────────────────────────────────────────────┘
```

1. **Bảng `Transactions` (Quản lý Thu/Chi):**
   - `PK`: `user_id` (String) — Định danh người dùng.
   - `SK`: `tx_{timestamp}_{uuid}` (String) — Khóa sắp xếp theo thời gian giao dịch.
   - *Thuộc tính:*
     - `amount`: Số tiền giao dịch (lưu dưới dạng chuỗi hoặc số tương thích Python `Decimal`).
     - `category`: Danh mục chi tiêu (Ăn uống, Đi lại, Hóa đơn, Tiết kiệm, v.v.).
     - `description`: Mô tả chi tiết giao dịch.
     - `type`: Loại giao dịch (`expense` hoặc `income`).
     - `date`: Thời gian phát sinh (ISO-8601).
     - `path_source`: Nhãn định tuyến thực thi (`fast_path_system1` hoặc `reasoning_path_llm`).
     - `s3_receipt_key`: Đường dẫn tham chiếu ảnh hóa đơn trên Amazon S3 (nếu có).
     - `created_at`: Thời điểm lưu bản ghi.

2. **Bảng `Tasks` (Quản lý Công việc & Ma trận Ưu tiên):**
   - `PK`: `user_id` (String).
   - `SK`: `task_{timestamp}_{uuid}` (String).
   - *Thuộc tính:*
     - `title`: Tên công việc/nhiệm vụ.
     - `deadline`: Hạn chót hoàn thành (ISO-8601 UTC).
     - `priority`: Mức độ ưu tiên theo Ma trận Ưu tiên Động (`high`, `medium`, `low`).
     - `status`: Trạng thái thực thi (`pending` hoặc `completed`).
     - `tags`: Nhãn phân loại công việc (Ví dụ: `["work", "project-ai", "urgent"]`).
     - `created_at`, `completed_at`: Mốc thời gian tạo và hoàn thành nhiệm vụ.

3. **Bảng `Sessions` (Agent Memory & Kev Telemetry Logs):**
   - `PK`: `user_id` (String).
   - `SK`: `session_{session_id}` (String).
   - *Thuộc tính:*
     - `chat_history`: Lịch sử các lượt tương tác trong phiên hội thoại.
     - `agent_memory`: Bộ nhớ dài hạn lưu sở thích, quy tắc chi tiêu cá nhân, ngữ cảnh công việc.
     - `telemetry_logs`: Nhật ký vận hành mô hình Kev System 1 và LLM (độ trễ phản hồi từng request tính bằng `ms`, điểm tin cậy `confidence`, số lượng token đã tiết kiệm `tokens_saved`, model ID sử dụng).

4. **Bảng `SavingsGoals` (Quỹ Tiết kiệm Tích lũy):**
   - `PK`: `user_id` (String).
   - `SK`: `goal_{goal_id}` (String).
   - *Thuộc tính:*
     - `goal_name`: Tên mục tiêu tích lũy (Ví dụ: *"Mua laptop 35tr"*).
     - `target_amount`: Số tiền mục tiêu cần đạt (`Decimal`).
     - `current_amount`: Số tiền đã nạp vào quỹ hiện tại (`Decimal`).
     - `deadline`: Hạn chót hoàn thành mục tiêu.
     - `progress_percentage`: Tỷ lệ phần trăm đã đạt ($100 \times \frac{\text{current}}{\text{target}}$).
     - `status`: Trạng thái (`active` hoặc `reached`).

#### 2.2. Tầng Lưu Trữ Blob Storage Trên Amazon S3 & Temp Audio Pipeline
- **Bucket cấu hình:** `s3://onis-media-{user_id}/`
- **Phân vùng đối tượng (Prefixes):**
  - `receipts/{tx_id}/image.jpg`: Lưu ảnh chụp hóa đơn gốc và tài liệu sao kê PDF.
  - `temp_audio/{session_id}/{audio_id}.wav`: **Lưu đệm âm thanh tạm thời (Temp Audio Buffer)** nhận từ Web Speech / Micro trước khi truyền tới dịch vụ Speech-to-Text (STT) hoặc file âm thanh phát ra từ Text-to-Speech (TTS).
- **Chính sách Vòng đời (S3 Lifecycle Rules):**
  - Tất cả các đối tượng dưới tiền tố `temp_audio/` được gán quy tắc tự động xóa vĩnh viễn (Expiration Action) sau **24 đến 48 giờ**.
  - Lợi ích: Triệt tiêu chi phí lưu trữ tích tụ, bảo vệ quyền riêng tư cá nhân và bảo đảm tuân thủ nguyên tắc bảo mật dữ liệu âm thanh người dùng.

#### 2.3. Cơ Chế Đồng Bộ Cục Bộ (Local Sync Fallback)
Nhằm hỗ trợ quá trình phát triển, kiểm thử unit test và chế độ chạy ngoại tuyến (offline-first):
- **Tệp dữ liệu cục bộ `data/onis_db.json`:**
  - Định dạng JSON phân cấp phản chiếu 4 nhóm dữ liệu DynamoDB: `transactions`, `tasks`, `sessions` và `savings_goals`; telemetry thuộc dữ liệu phiên, không phải bảng nghiệp vụ thứ năm.
  - Được quản lý bởi lớp trừu tượng `src/database/local_storage.py`.
- **Nhắc nhở và cảnh báo bất thường:** Được tạo từ hạn mục tiêu trong `SavingsGoals` và dữ liệu giao dịch trong `Transactions`; không tạo thêm bảng DynamoDB nghiệp vụ.
- **Cơ chế chuyển đổi trong suốt (Transparent Repository Pattern):**
  - Cấu hình qua biến môi trường `DATA_SOURCE=dynamodb` hoặc `DATA_SOURCE=json`.
  - Khi không có AWS credentials hoặc mất kết nối mạng, hệ thống tự động fallback sang `local_storage.py` mà không làm thay đổi bất kỳ logic nghiệp vụ nào của các Agent hay Tools.

---

### 3. Options Considered & Rejection Reasons (Các phương án & Lý do bác bỏ)

| Phương án | Ưu điểm (Pros) | Nhược điểm (Cons) | Lý do bác bỏ / lựa chọn |
|---|---|---|---|
| **Option A: RDBMS Truyền Thống (PostgreSQL / MySQL Đơn Lẻ)** | Hỗ trợ ACID mạnh mẽ, truy vấn JOIN phức tạp thuận tiện. | Chi phí vận hành máy chủ cố định (always-on); không tối ưu cho kiến trúc serverless pay-as-you-go; khó lưu trữ trực tiếp file audio/ảnh lớn. | **BÁC BỎ:** Chi phí cố định cao khi hệ thống ở trạng thái nhàn rỗi; không tận dụng được tính co giãn tự động của AWS Serverless. |
| **Option B: DynamoDB Thuần Túy (Lưu File/Audio nhị phân vào Item)** | Một kho lưu trữ duy nhất, không cần quản lý S3 bucket. | Vượt ngưỡng 400 KB/item; chi phí RCU/WCU tăng đột biến; hiệu năng đọc ghi suy giảm nghiêm trọng. | **BÁC BỎ:** Anti-pattern rõ rệt trong thiết kế CSDL NoSQL; không đáp ứng được yêu cầu đệm file âm thanh Voice-First. |
| **Option C: Hybrid Storage (DynamoDB + S3 + Local Sync Fallback)** | Tối ưu chi phí serverless; độ trễ đọc/ghi < 10 ms; lưu trữ blob/audio không giới hạn; tự động dọn dẹp file tạm; hỗ trợ offline-first qua JSON/SQLite. | Cần cài đặt layer điều phối liên kết khóa tham chiếu (`s3_receipt_key`) và duy trì repository hai chế độ. | **ĐƯỢC CHỌN:** Giải pháp toàn diện nhất, đồng bộ hoàn hảo với Đề cương chi tiết và yêu cầu kỹ thuật đa nền tảng. |

---

### 4. Directives & Rules (Quy định bắt buộc)

- **MUST (Khóa phân vùng user_id):** Tất cả các bảng trên DynamoDB MUST sử dụng `user_id` làm Partition Key (PK) để bảo đảm nguyên tắc cô lập dữ liệu người dùng tuyệt đối.
- **MUST NOT (Cấm nhúng Binary vào DynamoDB):** Codebase MUST NOT lưu trữ trực tiếp ảnh Base64, file tài liệu nhị phân hoặc file âm thanh WAV/MP3 vào DynamoDB items.
- **MUST (Lưu trữ tham chiếu S3):** DynamoDB chỉ được phép lưu đường dẫn tham chiếu dạng chuỗi `s3_receipt_key` hoặc URL có chữ ký (Pre-signed URL) trỏ tới Amazon S3.
- **MUST (S3 Temp Audio Lifecycle):** Tất cả các file âm thanh ghi âm tạm thời từ tính năng Voice-First lưu trên S3 MUST được đặt dưới tiền tố `temp_audio/` và MUST có cấu hình S3 Lifecycle Rule tự động xóa sau tối đa 48 giờ.
- **MUST (Local Fallback Compatibility):** Lớp truy xuất dữ liệu (`src/database/`) MUST bảo đảm tính tương thích giao diện 1:1 giữa DynamoDB Client và Local JSON Storage (`data/onis_db.json`), cho phép toàn bộ hệ thống hoạt động trơn tru trong môi trường offline mà không cần AWS credentials.
- **ALWAYS (Nhãn nguồn gốc path_source):** Khi ghi bản ghi giao dịch mới vào bảng `Transactions`, hệ thống ALWAYS phải gắn nhãn nguồn gốc thực thi `path_source` (`fast_path_system1` hoặc `reasoning_path_llm`) để phục vụ đo đạc Kev Telemetry và đối soát hệ thống.

---

### 5. Consequences & Acceptance Criteria (Hệ quả & Tiêu chuẩn nghiệm thu)

#### A. Lợi ích đạt được
- **Độ trễ truy vấn siêu tốc:** Thời gian đọc/ghi dữ liệu có cấu trúc trên DynamoDB đạt mục tiêu $< 10$ ms.
- **Tối ưu chi phí:** Chi phí lưu trữ gần như bằng 0 trong giai đoạn phát triển và co giãn linh hoạt theo lưu lượng thực tế.
- **Bảo mật và riêng tư âm thanh:** Việc tự động dọn dẹp Temp Audio sau 24-48 giờ bảo đảm tuân thủ các quy định nghiêm ngặt về bảo vệ dữ liệu cá nhân.
- **Linh hoạt trong phát triển:** Nhà phát triển có thể chạy trọn vẹn demo trên máy cục bộ với `data/onis_db.json` mà không cần tài khoản AWS.

#### B. Đánh đổi & Thách thức
- Cần quản lý tính nhất quán giữa bản ghi DynamoDB và file nhị phân trên S3 (tránh mồ côi bản ghi khi upload S3 thành công nhưng ghi DynamoDB thất bại).
- Cần duy trì schema đồng bộ giữa `data/onis_db.json` và cấu trúc các bảng DynamoDB.

#### C. Tiêu chuẩn nghiệm thu (Acceptance Criteria)
1. **Khởi tạo đầy đủ 4 bảng:** DynamoDB hoặc local schema khởi tạo thành công 4 cấu trúc dữ liệu: `Transactions`, `Tasks`, `Sessions`, `SavingsGoals`.
2. **Kiểm tra Temp Audio Buffer:** File ghi âm giọng nói tạm thời được đẩy vào S3/local cache thành công và tự động xóa sau thời gian hết hạn cấu hình (Lifecycle Rule hoạt động đúng).
3. **Chuyển đổi nguồn dữ liệu trơn tru:** Chạy toàn bộ bộ test `pytest` thành công trên cả 2 chế độ `DATA_SOURCE=json` và `DATA_SOURCE=dynamodb`.
4. **Không vượt giới hạn kích thước Item:** Kích thước bản ghi trong DynamoDB kiểm tra luôn $< 10$ KB đối với mọi item giao dịch và task.

---

### 6. Revisit Triggers (Điều kiện xem xét lại)

Quyết định kiến trúc này cần được đánh giá lại khi:
1. Chi phí vận hành DynamoDB và S3 vượt ngưỡng ngân sách dự án (> $20/tháng).
2. Phát sinh nhu cầu thực hiện các truy vấn phân tích liên bảng phức tạp (Cross-table Analytics / OLAP) vượt quá năng lực của DynamoDB Secondary Indexes.
3. Dung lượng file âm thanh tạm thời tăng đột biến gây tắc nghẽn băng thông upload của người dùng trên thiết bị mạng yếu.

---

Nhận xét cuối cùng: Kiến trúc lưu trữ lai DynamoDB + S3 kết hợp cơ chế Local Sync qua `data/onis_db.json` mang lại sự cân bằng lý tưởng giữa khả năng mở rộng không giới hạn của Cloud Serverless và tính tiện lợi, độc lập của môi trường phát triển cục bộ.
