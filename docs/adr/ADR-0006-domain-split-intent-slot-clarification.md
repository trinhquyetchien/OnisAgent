---
id: ADR-0006
timestamp: 2026-11-14T20:30:00Z
status: accepted
deciders: Trịnh Quyết Chiến, Hứa Huỳnh Anh
tags:
  - onisagent
  - domain-split
  - intent-schema
  - slot-validation
  - clarification-dialog
  - finance-domain
  - task-domain
related_adrs: [ADR-0002, ADR-0004]
---

# ADR-0006: Phân Tách Miền Nghiệp Vụ (Finance vs. Task), Đặc Tả Intent-Slot Schema & Cơ Chế Hỏi Làm Rõ (Clarification)

> **Y-Statement:** Trong bối cảnh OnisAgent phục vụ 2 nghiệp vụ cốt lõi là Quản lý Tài chính cá nhân và Quản lý Công việc/Deadline, đối mặt với vấn đề đầu vào giọng nói/văn bản người dùng thường xuyên bị thiếu thông tin quan trọng (ví dụ: thiếu số tiền, thiếu hạn chót, không rõ tài khoản/ví nào), chúng tôi quyết định **Phân tách hoàn toàn 2 miền dữ liệu (Finance Domain & Task Domain)**, chuẩn hóa tiền tố intent (`finance.*` và `task.*`), đồng thời thiết lập **Hệ thống Kiểm duyệt Slot (Slot Validator & Clarification Engine)** với nguyên tắc:
> 1. Phân chia rõ ràng trường **BẮT BUỘC (Required Slots)** và trường **TÙY CHỌN (Optional Slots)** cho từng Intent.
> 2. Khi phát hiện thiếu trường bắt buộc hoặc độ tin cậy thấp, hệ thống chặn ghi và tự động chuyển sang trạng thái `NEED_CLARIFICATION` để chủ động hỏi lại người dùng kèm gợi ý chọn nhanh (Quick-reply options).
> 3. Tự động áp dụng giá trị mặc định an toàn (Fallback Defaults) cho các trường tùy chọn nhằm giảm thiểu tối đa ma sát nhập liệu.

---

## 1. Bối Cảnh & Vấn Đề (Context & Problem)

Khi người dùng ra lệnh bằng giọng nói tự nhiên hoặc gõ nhanh trên điện thoại/web:
1. **Thiếu thông tin sống còn:**
   * Nói: *"Vừa mua áo sơ mi"* $\rightarrow$ Thiếu số tiền (`amount`), không thể ghi sổ chi tiêu.
   * Nói: *"Nhắc tôi nộp báo cáo"* $\rightarrow$ Thiếu mốc thời gian (`deadline`), không thể lên lịch nhắc nhở chính xác.
2. **Mơ hồ tài khoản khi người dùng có nhiều ví:**
   * Người dùng có Ví tiền mặt, Vietcombank, Momo nhưng chỉ bảo: *"Chi 50k ăn phở"* $\rightarrow$ Cần cơ chế xác định trừ ví nào hoặc dùng ví mặc định.
3. **Lẫn lộn dữ liệu giữa Tài chính và Công việc:**
   * Việc gộp chung một schema dẫn đến khó bảo trì, khó scale mô hình Kev và làm phức tạp hóa tầng lưu trữ (CSDL).

---

## 2. Quyết Định Kiến Trúc (Architectural Decisions)

### 2.1. Phân Tách 2 Miền Nghiệp Vụ (Two-Domain Architecture)

Toàn bộ hệ thống OnisAgent từ tầng Model, Validation đến Data Tier được chia thành 2 miền độc lập:
* **Miền Tài Chính (`finance.*`):**
  * Dữ liệu: `Transactions`, `Accounts`, `SavingsGoals`, `LoanSchedules`.
  * Tính toán: 100% Python `Decimal` (AWS Lambda & Local Tools).
* **Miền Công Việc & Deadline (`task.*`):**
  * Dữ liệu: `Tasks`, `Categories`, `DeadlineTrackers`.
  * Tính toán: Xử lý múi giờ địa phương (`Asia/Ho_Chi_Minh`), phân loại mức ưu tiên (Eisenhower Matrix).

```
                          [ Input Câu Lệnh Người Dùng ]
                                        │
                                        ▼
                         [ Domain Router / Kev Classifier ]
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
         [ 💰 FINANCE DOMAIN ]                    [ 📋 TASK DOMAIN ]
    • finance.expense.create                 • task.create
    • finance.income.create                  • task.complete
    • finance.balance.query                  • task.query
    • finance.loan.calculate                 • task.delete
    • finance.savings.create                 • task.plan.escalate
    • finance.analysis.escalate                             │
                    │                                       │
                    ▼                                       ▼
        [ Finance Slot Validator ]              [ Task Slot Validator ]
        - Thiếu amount? -> Hỏi số tiền          - Thiếu title? -> Hỏi tên task
        - Thiếu tài khoản? -> Gợi ý ví          - Thiếu deadline? -> Gợi ý đặt giờ
                    │                                       │
                    └───────────────────┬───────────────────┘
                                        ▼
                  [ Đủ thông tin: Thực thi / Lưu trữ riêng biệt ]
```

---

## 3. Bảng Đặc Tả Chi Tiết Intent & Slot Schema

### 3.1. Miền Tài Chính (Finance Domain)

| Intent | Ý nghĩa | Trường BẮT BUỘC | Trường TÙY CHỌN | Giá trị Mặc định (Fallback) | Câu hỏi làm rõ mẫu (Clarification Dialog) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`finance.expense.create`** | Ghi nhận khoản chi | • `amount` (tiền)<br>• `category` hoặc `note` | • `account`<br>• `date`<br>• `payment_method` | • `account`: `default_account`<br>• `date`: `now` | *"Bạn đã chi bao nhiêu tiền cho khoản [nội dung] này vậy?"* |
| **`finance.income.create`** | Ghi nhận khoản thu | • `amount` (tiền) | • `source`<br>• `account`<br>• `date` | • `account`: `default_account`<br>• `date`: `now`<br>• `source`: "Thu nhập khác" | *"Bạn đã nhận được số tiền là bao nhiêu từ [nguồn]?"* |
| **`finance.balance.query`** | Tra cứu số dư ví | *Không có* | • `account` | • `account`: `all` (tất cả các ví) | *"Bạn muốn kiểm tra số dư của tài khoản nào (Ví tiền mặt, Ngân hàng hay Tất cả)?"* |
| **`finance.loan.calculate`**| Dự toán lịch trả góp khoản vay | • `principal`<br>• `term_months`<br>• `annual_rate` | • `method`<br>• `purpose` | • `method`: `dư nợ giảm dần` | • Thiếu tiền: *"Bạn cần tính vay số tiền bao nhiêu?"*<br>• Thiếu tháng: *"Thời hạn trả góp là mấy tháng?"*<br>• Thiếu lãi: *"Lãi suất vay là bao nhiêu %/năm?"* |
| **`finance.savings.create`**| Tạo quỹ tiết kiệm | • `goal_name`<br>• `target_amount` | • `deadline`<br>• `monthly_contribution` | • `deadline`: Không giới hạn | *"Mục tiêu tiết kiệm [tên mục tiêu] cần số tiền bao nhiêu?"* |
| **`finance.analysis.escalate`** | Tư vấn & phân tích dòng tiền (LLM) | • `query` (nội dung câu hỏi) | • `period` | • `period`: Tháng hiện tại | Chuyển ngữ cảnh cho `FinancialAdvisoryAgent` |

### 3.2. Miền Công Việc & Deadline (Task Domain)

| Intent | Ý nghĩa | Trường BẮT BUỘC | Trường TÙY CHỌN | Giá trị Mặc định (Fallback) | Câu hỏi làm rõ mẫu (Clarification Dialog) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`task.create`** | Tạo việc / nhắc nhở | • `title` (tiêu đề việc) | • `deadline`<br>• `priority`<br>• `category`<br>• `reminder` | • `priority`: `medium`<br>• `category`: "Chung"<br>• `deadline`: `null` (hỏi nhẹ hoặc bỏ trống) | Nếu input không có tên việc: *"Bạn cần tạo công việc với nội dung gì?"*<br>Nếu chưa có giờ: *"Bạn có muốn đặt hạn chót (deadline) cho việc này không?"* |
| **`task.complete`** | Đánh dấu hoàn thành | • `title` hoặc `task_id` | • `completion_date` | • `completion_date`: `now` | *"Bạn muốn đánh dấu hoàn thành công việc nào?"* (kèm danh sách việc đang chờ) |
| **`task.query`** | Tra cứu danh sách việc | *Không có* | • `time_range`<br>• `status`<br>• `priority` | • `time_range`: `today`<br>• `status`: `pending` | Tự động trả về danh sách task hôm nay chưa hoàn tất (không cần hỏi lại) |
| **`task.delete`** | Hủy hoặc xóa công việc | • `title` hoặc `task_id` | *Không có* | *Không có* | *"Bạn muốn xóa công việc nào?"* (Kích hoạt HITL Gate 3 xác nhận trước khi xóa) |
| **`task.plan.escalate`** | Lập kế hoạch ngày/tuần (LLM) | • `time_frame` | • `focus_goal` | • `time_frame`: Hôm nay | Chuyển ngữ cảnh cho `TaskManagerAgent` phân loại Eisenhower |

---

## 4. Cơ Chế Hội Thoại Làm Rõ (Clarification Dialog Flow)

1. **Phát hiện thiếu:**
   Khi `Kev Inference Handler` hoặc Policy Engine phân tích input:
   * Nếu thiếu `Required Slots`: Không gọi hàm execute, trả về payload dạng:
     ```json
     {
       "status": "NEED_CLARIFICATION",
       "intent": "finance.expense.create",
       "missing_slot": "amount",
       "message": "Bạn đã chi cho trà sữa hết bao nhiêu tiền?",
       "expected_type": "currency",
       "quick_replies": ["30.000₫", "45.000₫", "60.000₫"]
     }
     ```
2. **Context Retention (Giữ ngữ cảnh đàm thoại):**
   * Session State lưu lại các slot đã nhận diện được trước đó (`note: "trà sữa"`, `category: "đồ uống"`).
   * Lượt tiếp theo người dùng chỉ cần nhập *"45k"*, hệ thống tự động merge dữ liệu và hoàn tất giao dịch.
3. **UI/UX Tương tác thông minh:**
   * Giao diện Flutter Web/App hiển thị câu hỏi và các **Quick-Reply Action Chips** để người dùng có thể chạm 1 chạm thay vì phải gõ lại.

---

## 5. Hệ Quả & Lộ Trình Triển Khai (Consequences & Next Steps)

* **Ưu điểm:**
  * Giảm triệt để việc ghi nhận dữ liệu "rác" hoặc thiếu trường cốt lõi vào database.
  * Trải nghiệm mượt mà, tự nhiên: người dùng có thể ra lệnh ngắn, app chủ động hỏi lại lịch sự và thông minh.
  * Tách biệt rõ ràng 2 domain giúp phát triển độc lập cả frontend lẫn backend.
* **Các bước triển khai tiếp theo:**
  1. Cập nhật nhãn chuẩn trong tập dữ liệu Kev Dataset (`backend/data/`).
  2. Xây dựng module `SlotValidator` trong `backend/src/utils/` hoặc `backend/src/agents/`.
  3. Tích hợp giao thức phản hồi `NEED_CLARIFICATION` vào Backend API và UI Flutter.
