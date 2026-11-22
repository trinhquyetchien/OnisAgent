# OnisAgent – Danh Mục Intent & Đặc Tả Slot Toàn Diện (Extended Intent Catalog & Slot Specification)

> **Tài liệu đặc tả chuẩn hóa 33 Intent chuyên sâu cho OnisAgent Core Engine**  
> Bao quát 4 nhóm: **Miền Tài Chính (Finance)**, **Miền Công Việc & Thời Gian (Task & Schedule)**, **Giao Thoa Miền (Cross-Domain)** và **Hệ Thống (System)**.  
> Tuân thủ các nguyên tắc [ADR-0001](file:///home/trinhquyetchien/Projects/Main/Team/OnisAgent/docs/adr/ADR-0001-decimal-money-calculation.md), [ADR-0004](file:///home/trinhquyetchien/Projects/Main/Team/OnisAgent/docs/adr/ADR-0004-human-in-the-loop-workflow.md) và [ADR-0006](file:///home/trinhquyetchien/Projects/Main/Team/OnisAgent/docs/adr/ADR-0006-domain-split-intent-slot-clarification.md).

---

## 📑 Bảng Tra Cứu Toàn Bộ 33 Intent (Master Intent Catalog)

| STT | Domain | Mã Intent Chuẩn | Ý Nghĩa / Mục Đích | Tuyến Xử Lý | HITL Gate |
| :---: | :---: | :--- | :--- | :---: | :---: |
| **1** | 💰 Finance | `finance.get_balance` | Tra cứu số dư ví / tài sản hiện có | **Fast Path** (~5-12ms) | None |
| **2** | 💰 Finance | `finance.add_expense` | Ghi nhận chi tiêu thường nhật | **Fast Path** (~5-12ms) | Gate 2 |
| **3** | 💰 Finance | `finance.add_income` | Ghi nhận thu nhập | **Fast Path** (~5-12ms) | None |
| **4** | 💰 Finance | `finance.transfer` | Chuyển tiền giữa các ví / Nạp rút ATM | **Fast Path** (~5-12ms) | None |
| **5** | 💰 Finance | `finance.record_debt` | Ghi sổ nợ / cho mượn tiền | **Fast Path** (~5-12ms) | Gate 2 |
| **6** | 💰 Finance | `finance.debt_repay` | Trả nợ / Ghi nhận thu nợ về | **Fast Path** (~5-12ms) | None |
| **7** | 💰 Finance | `finance.query_debt` | Tra cứu sổ nợ & danh sách ai nợ ai | **Fast Path** (~5-12ms) | None |
| **8** | 💰 Finance | `finance.split_bill` | Chia tiền hóa đơn nhóm / đi chơi | **Fast Path** + Decimal | None |
| **9** | 💰 Finance | `finance.pay_bill` | Đóng tiền hóa đơn định kỳ (điện, nước, trọ) | **Fast Path** (~5-12ms) | None |
| **10** | 💰 Finance | `finance.query_transactions` | Tra cứu / Lọc lịch sử chi tiêu theo kỳ/danh mục | **Fast Path** (~5-12ms) | None |
| **11** | 💰 Finance | `finance.budget_plan` | Thiết lập hạn mức chi tiêu / ngân sách | **Reasoning Path** (Bedrock) | Gate 1 |
| **12** | 💰 Finance | `finance.update_budget` | Điều chỉnh hạn mức ngân sách đã có | **Fast Path** (~5-12ms) | Gate 1 |
| **13** | 💰 Finance | `finance.loan_installment_plan` | Dự toán bảng khấu hao trả góp khoản vay | **Fast Path** + Decimal | Gate 1 |
| **14** | 💰 Finance | `finance.savings_goal` | Tạo quỹ tiết kiệm / mục tiêu tài chính | **Fast Path** (~5-12ms) | Gate 1 |
| **15** | 💰 Finance | `finance.financial_report` | Báo cáo tài chính & phân tích dòng tiền sâu | **Reasoning Path** (Bedrock) | None |
| **16** | 📋 Task | `task.create` | Thêm công việc / Việc cần làm | **Fast Path** (~5-12ms) | None |
| **17** | 📋 Task | `task.create_recurring` | Công việc / Thói quen lặp lại chu kỳ | **Fast Path** (~5-12ms) | None |
| **18** | 📋 Task | `task.query_today` | Danh sách công việc hôm nay / Kế hoạch ngày | **Fast Path** (~5-12ms) | None |
| **19** | 📋 Task | `task.query_deadline` | Cảnh báo / Tra cứu hạn chót deadline gấp | **Fast Path** (~5-12ms) | None |
| **20** | 📋 Task | `task.query_by_tag` | Lọc việc theo nhãn / dự án (AI4Life, cá nhân) | **Fast Path** (~5-12ms) | None |
| **21** | 📋 Task | `task.query_completed` | Xem lại các công việc đã hoàn thành | **Fast Path** (~5-12ms) | None |
| **22** | 📋 Task | `task.schedule_event` | Lịch hẹn / Cuộc họp / Sự kiện có giờ | **Fast Path** (~5-12ms) | None |
| **23** | 📋 Task | `task.reschedule` | Dời lịch / Đổi hạn chót / Hoãn giờ | **Fast Path** (~5-12ms) | None |
| **24** | 📋 Task | `task.plan_schedule` | Lập kế hoạch ngày/tuần (Eisenhower Matrix) | **Reasoning Path** (Bedrock) | None |
| **25** | 📋 Task | `task.complete` | Đánh dấu hoàn thành việc | **Fast Path** (~5-12ms) | None |
| **26** | 📋 Task | `task.cancel` | Tạm hoãn / Hủy công việc (giữ vết lịch sử) | **Fast Path** (~5-12ms) | None |
| **27** | 📋 Task | `task.delete` | Xóa vĩnh viễn công việc | **Fast Path** (~5-12ms) | **Gate 3 (BLOCKED)** |
| **28** | 📋 Task | `task.search` | Tìm kiếm công việc theo từ khóa | **Fast Path** (~5-12ms) | None |
| **29** | 🔗 Cross | `cross.plan_expense_task` | Kế hoạch công việc gắn dự trù kinh phí | **Reasoning Path** (Bedrock) | Gate 1 |
| **30** | 🔗 Cross | `cross.bill_due_reminder` | Nhắc hạn thanh toán hóa đơn kèm số tiền | **Fast Path** (~5-12ms) | None |
| **31** | ⚙️ System | `system.greeting_summary` | Chào buổi sáng & Tóm tắt số dư + top task | **Fast Path** (~5-12ms) | None |
| **32** | ⚙️ System | `system.help` | Hướng dẫn khả năng & mẫu câu của trợ lý | **Fast Path** (~5-12ms) | None |
| **33** | ⚙️ System | `system.undo` | Hoàn tác thao tác vừa thực hiện | **Fast Path** (~5-12ms) | Gate 2 |

---

# 💰 1. MIỀN TÀI CHÍNH NÂNG CAO (FINANCE ADVANCED)

### 1.1. `finance.transfer` – Chuyển tiền giữa các ví / Nạp rút tiền
* **Mục đích:** Luân chuyển số dư giữa các tài khoản nội bộ (vd: từ Vietcombank sang ví Momo, hoặc rút tiền ATM về ví tiền mặt).
* **Đường dẫn:** **Fast Path (System 1)**.
* **Mức độ HITL:** `None`.
* **Slots:**
  * `amount` (`Decimal`, **Bắt buộc**): Số tiền cần chuyển.
  * `from_account` (`str`, **Bắt buộc**): Tài khoản nguồn trừ tiền.
  * `to_account` (`str`, **Bắt buộc**): Tài khoản đích nhận tiền.
  * `fee` (`Decimal`, Tùy chọn, fallback `0`): Phí chuyển tiền nếu có.
  * `date` (`datetime`, Tùy chọn, fallback `now`).
* **Chiến lược làm rõ:**
  * Thiếu `amount`: *"Bạn muốn chuyển số tiền là bao nhiêu?"* $\rightarrow$ `["200.000₫", "500.000₫", "1.000.000₫", "2.000.000₫"]`
  * Thiếu `to_account`: *"Bạn muốn chuyển tiền đến ví hoặc tài khoản nào?"* $\rightarrow$ `["Ví Momo", "Ví Tiền mặt", "Vietcombank", "MB Bank"]`
* **Mẫu câu thực tế:**
  1. *"Chuyển 500k từ Vietcombank sang ví Momo giúp mình"*
  2. *"Rút 2 củ từ ATM về ví tiền mặt"*
  3. *"Nạp 1 triệu từ tài khoản ngân hàng vào ví điện tử ZaloPay"*
  4. *"Bắn 300k từ Momo qua MB Bank"*
  5. *"Chuyển 5 củ từ tài khoản lương sang tài khoản tiết kiệm"*
  6. *"Rút 5 xị tiền mặt tiêu vặt"*
  7. *"Nạp 200 nghìn vào ShopeePay từ VCB"*
  8. *"Chuyển 1tr2 từ quỹ chung sang ví cá nhân"*

---

### 1.2. `finance.record_debt` – Quản lý nợ / Cho mượn tiền
* **Mục đích:** Ghi nhận khoản tiền cho người khác vay mượn hoặc khoản tiền mình đi vay từ người khác.
* **Đường dẫn:** **Fast Path (System 1)**.
* **Mức độ HITL:** `Gate 2` (Đính chính thông tin người nợ/con nợ).
* **Slots:**
  * `amount` (`Decimal`, **Bắt buộc**): Số tiền vay/cho mượn.
  * `person` (`str`, **Bắt buộc**): Tên người liên quan.
  * `debt_type` (`str`, **Bắt buộc**): `"lend"` (cho mượn) hoặc `"borrow"` (đi mượn).
  * `due_date` (`datetime`, Tùy chọn): Ngày hẹn trả.
  * `note` (`str`, Tùy chọn): Lý do mượn tiền.
* **Chiến lược làm rõ:**
  * Thiếu `person`: *"Khoản tiền này bạn cho ai mượn hoặc mượn từ ai vậy?"*
  * Thiếu `amount`: *"Số tiền mượn/cho mượn là bao nhiêu?"* $\rightarrow$ `["50.000₫", "100.000₫", "500.000₫", "1.000.000₫"]`
* **Mẫu câu thực tế:**
  1. *"Cho thằng Nam mượn 500k hẹn cuối tháng trả"*
  2. *"Mượn anh Tuấn 2 xị ăn trưa mai trả"*
  3. *"Ghi sổ cho Lan vay 2 củ đóng tiền phòng"*
  4. *"Vừa vay mẹ 5 triệu mua laptop"*
  5. *"Thằng Huy mượn 300 ngàn đổ xăng"*
  6. *"Cho bạn cùng phòng vay 1 triệu tiền ăn"*
  7. *"Mượn tiền đứa bạn 150k mua sách"*
  8. *"Ghi nợ cái Hằng 450k tiền vé xem phim"*

---

### 1.3. `finance.debt_repay` – Trả nợ / Ghi nhận thu nợ về
* **Mục đích:** Cập nhật hoặc tất toán khoản nợ khi người khác trả tiền cho mình hoặc khi mình thanh toán nợ cho người khác.
* **Đường dẫn:** **Fast Path (System 1)**.
* **Slots:**
  * `amount` (`Decimal`, **Bắt buộc**): Số tiền trả nợ.
  * `person` (`str`, **Bắt buộc**): Tên người trả hoặc người nhận.
  * `account` (`str`, Tùy chọn, fallback `"default_account"`).
* **Mẫu câu thực tế:**
  1. *"Thằng Nam vừa trả 500k tiền nợ hôm bữa"*
  2. *"Đã trả 2 xị cho anh Tuấn tiền ăn trưa"*
  3. *"Lan chuyển khoản trả 2 củ tiền phòng rồi"*
  4. *"Vừa gửi trả mẹ 5 triệu tiền vay"*
  5. *"Thu được nợ 300k từ thằng Huy"*
  6. *"Đã thanh toán nợ 150k tiền sách cho bạn"*
  7. *"Cái Hằng trả lại 450k tiền vé xem phim qua Momo"*
  8. *"Ghi nhận nhận lại tiền nợ 1 triệu"*

---

### 1.3b. `finance.query_debt` – Tra cứu sổ nợ & các khoản cho vay / mượn tiền
* **Mục đích:** Tra cứu danh sách các khoản người khác đang nợ mình, các khoản mình đang vay nợ người khác, hoặc kiểm tra dư nợ cụ thể với một người.
* **Đường dẫn:** **Fast Path (~6ms)**.
* **Quyền HITL:** Không yêu cầu (`None`).
* **Slots:**
  * `debt_type` (`str`, Tùy chọn, mặc định `"all"`): Loại nợ cần lọc (`"borrow"`: tôi đang nợ người khác, `"lend"`: người khác đang nợ tôi, `"all"`: toàn bộ sổ nợ).
  * `person` (`str`, Tùy chọn, mặc định `None`): Tên người cụ thể cần kiểm tra dư nợ (ví dụ: `"Tuấn"`, `"Hải"`).
* **Mẫu câu thực tế:**
  1. *"Tôi có nợ ai không"*
  2. *"Tôi đang nợ những ai vậy"*
  3. *"Check xem tôi nợ ai"*
  4. *"Có ai vay tiền tôi không"*
  5. *"Ai đang mượn tiền tôi chưa trả"*
  6. *"Thằng Tuấn có nợ tôi đồng nào không"*
  7. *"Hải còn nợ tôi tiền không"*
  8. *"Xem danh sách cho mượn tiền và mượn nợ"*
  9. *"Tổng tiền người ta nợ tôi là bao nhiêu"*
  10. *"Hôm nay có khoản nợ nào cần đòi không"*

---

### 1.4. `finance.split_bill` – Chia tiền nhóm / Chia hóa đơn
* **Mục đích:** Tính toán số tiền mỗi thành viên phải trả khi đi ăn uống, du lịch nhóm và tạo các khoản nợ tương ứng.
* **Đường dẫn:** **Fast Path** + **Deterministic Decimal Calculator**.
* **Slots:**
  * `total_amount` (`Decimal`, **Bắt buộc**): Tổng giá trị hóa đơn.
  * `members_count` (`int`, **Bắt buộc**): Số người cùng chia.
  * `description` (`str`, Tùy chọn, fallback `"Hóa đơn chung"`).
  * `my_share` (`Decimal`, Tùy chọn, tự tính toán).
* **Chiến lược làm rõ:**
  * Thiếu `members_count`: *"Hóa đơn này chia đều cho bao nhiêu người vậy bạn?"* $\rightarrow$ `["2 người", "3 người", "4 người", "5 người"]`
* **Mẫu câu thực tế:**
  1. *"Hóa đơn lẩu 1tr2 chia đều cho 4 người"*
  2. *"Ăn trưa hết 350k chia 5 người thì mỗi người bao nhiêu"*
  3. *"Tiền phòng karaoke 800 nghìn share cho 4 đứa"*
  4. *"Đi cà phê hết 180k chia 3"*
  5. *"Tính tiền ăn uống 2 triệu rưỡi chia 6 người"*
  6. *"Hóa đơn Grab 90k chia đôi với Nam"*
  7. *"Tiền homestay Đà Lạt 3 củ chia cho 5 người"*
  8. *"Chia tiền tiệc sinh nhật 4 triệu 8 người"*

---

### 1.5. `finance.pay_bill` – Đóng tiền hóa đơn định kỳ
* **Mục đích:** Thanh toán các chi phí sinh hoạt định kỳ (tiền phòng trọ, điện, nước, internet, rác).
* **Đường dẫn:** **Fast Path (System 1)**.
* **Slots:**
  * `amount` (`Decimal`, **Bắt buộc**): Số tiền hóa đơn.
  * `bill_type` (`str`, **Bắt buộc**): `"điện"`, `"nước"`, `"internet"`, `"tiền phòng"`, `"học phí"`.
  * `account` (`str`, Tùy chọn, fallback `"default_account"`).
* **Mẫu câu thực tế:**
  1. *"Đóng tiền trọ tháng này 3 triệu 5"*
  2. *"Vừa thanh toán tiền điện 650k qua banking"*
  3. *"Đóng tiền nước tháng 11 hết 120 ngàn"*
  4. *"Nộp tiền mạng internet FPT 220k"*
  5. *"Đóng học phí kỳ 1 hết 11 củ"*
  6. *"Thanh toán hóa đơn truyền hình cáp 150k"*
  7. *"Vừa nộp tiền rác và phí chung cư 300k"*
  8. *"Đóng tiền phí giữ xe máy 120k"*

---

### 1.6. `finance.query_transactions` – Tra cứu / Lọc lịch sử chi tiêu
* **Mục đích:** Tìm kiếm và lọc danh sách các giao dịch thu chi trong quá khứ theo danh mục, thời gian, từ khóa.
* **Đường dẫn:** **Fast Path (System 1)**.
* **Slots:**
  * `category` (`str`, Tùy chọn): Danh mục cần lọc (`"ăn uống"`, `"nhà ở"`).
  * `time_range` (`str`, Tùy chọn, fallback `"this_month"`): `"hôm nay"`, `"tuần này"`, `"tháng trước"`.
  * `transaction_type` (`str`, Tùy chọn): `"expense"`, `"income"`, `"all"`.
* **Mẫu câu thực tế:**
  1. *"Tuần này tôi chi bao nhiêu tiền cà phê rồi?"*
  2. *"Xem lịch sử chi tiêu tiền ăn uống tháng này"*
  3. *"Tháng trước tôi kiếm được bao nhiêu tiền thu nhập"*
  4. *"Hôm qua tôi đã tiêu những khoản nào"*
  5. *"Lọc các giao dịch trên 1 triệu trong tháng"*
  6. *"Xem các khoản chi mua sắm quần áo tuần vừa rồi"*
  7. *"Liệt kê các khoản thu chi hôm nay"*
  8. *"Kiểm tra lịch sử đóng tiền học phí"*

---

### 1.7. `finance.financial_report` – Báo cáo tài chính & Phân tích chuyên sâu
* **Mục đích:** Tổng hợp dòng tiền, phân tích tỷ trọng chi tiêu (expense ratio), đánh giá sức khỏe tài chính và tư vấn tối ưu.
* **Đường dẫn:** **Reasoning Path (System 2)** – `FinancialAdvisoryAgent` via Amazon Bedrock.
* **Slots:**
  * `period` (`str`, Tùy chọn, fallback `"this_month"`): Khoảng thời gian phân tích.
  * `focus_area` (`str`, Tùy chọn): `"khoản chi lãng phí"`, `"tỷ lệ tiết kiệm"`, `"tổng thể"`.
* **Mẫu câu thực tế:**
  1. *"Báo cáo tài chính tháng này của tôi thế nào?"*
  2. *"Tháng này tôi phung phí ở đâu nhiều nhất?"*
  3. *"Phân tích tỷ trọng chi tiêu tuần này giúp mình"*
  4. *"So sánh chi tiêu tháng 11 với tháng 10 xem tăng giảm ra sao"*
  5. *"Tôi có đang chi tiêu vượt mức an toàn không"*
  6. *"Tổng kết dòng tiền thu chi quý vừa rồi"*
  7. *"Đánh giá tình hình tiết kiệm của tôi hiện tại"*
  8. *"Gợi ý cách cắt giảm chi tiêu để cuối năm dư 20 triệu"*

---

### 1.8. `finance.update_budget` – Điều chỉnh hạn mức ngân sách
* **Mục đích:** Nâng hoặc hạ trần ngân sách cho một danh mục khi kế hoạch tài chính thay đổi.
* **Đường dẫn:** **Fast Path (System 1)**.
* **Mức độ HITL:** `Gate 1`.
* **Slots:**
  * `category` (`str`, **Bắt buộc**): Danh mục cần chỉnh (`"ăn uống"`, `"mua sắm"`, `"tổng thể"`).
  * `new_limit` (`Decimal`, **Bắt buộc**): Hạn mức mới.
* **Mẫu câu thực tế:**
  1. *"Tăng ngân sách ăn uống tháng này lên 4 triệu"*
  2. *"Giảm hạn mức mua sắm xuống còn 1 củ"*
  3. *"Đổi ngân sách tổng chi tiêu tuần này thành 2tr5"*
  4. *"Chỉnh lại hạn mức tiền đi lại là 500k"*

---

# 📋 2. MIỀN CÔNG VIỆC & THỜI GIAN NÂNG CAO (TASK ADVANCED)

### 2.1. `task.create_recurring` – Công việc / Thói quen lặp lại
* **Mục đích:** Tạo thói quen hoặc nhiệm vụ tự động lặp lại theo chu kỳ (mỗi ngày, các thứ 2-4-6, mỗi tuần).
* **Đường dẫn:** **Fast Path (System 1)**.
* **Slots:**
  * `title` (`str`, **Bắt buộc**): Tên công việc/thói quen.
  * `recurrence` (`str`, **Bắt buộc**): Tần suất (`"daily"`, `"weekdays"`, `"weekly"`, `"t2_t4_t6"`).
  * `time_of_day` (`str`, Tùy chọn): Giờ thực hiện (vd: `"19:00"`, `"sáng"`).
* **Mẫu câu thực tế:**
  1. *"Nhắc tôi đi tập gym vào thứ 2, 4, 6 lúc 18h"*
  2. *"Đặt lịch uống thuốc mỗi ngày lúc 8h sáng"*
  3. *"Thêm thói quen đọc sách 30 phút mỗi tối 22h"*
  4. *"Nhắc dọn phòng vào mỗi sáng Chủ nhật"*
  5. *"Lập lịch học tiếng Anh hàng ngày 20h"*
  6. *"Nhắc sao lưu dữ liệu máy tính vào cuối mỗi tuần"*
  7. *"Mỗi sáng thứ Hai nhắc xem lại mục tiêu tuần"*
  8. *"Lên lịch tưới cây mỗi ngày lúc 17h chiều"*

---

### 2.2. `task.reschedule` – Dời lịch / Đổi hạn chót / Lùi giờ
* **Mục đích:** Thay đổi hạn chót (deadline) hoặc giờ hẹn của một công việc đã có từ trước.
* **Đường dẫn:** **Fast Path (System 1)**.
* **Slots:**
  * `title` (`str`, **Bắt buộc**): Tên công việc cần dời.
  * `new_deadline` (`datetime`, **Bắt buộc**): Thời gian mới.
* **Mẫu câu thực tế:**
  1. *"Dời deadline nộp slide đồ án sang 20h tối mai"*
  2. *"Hoãn cuộc họp nhóm sang 15h chiều thứ 4"*
  3. *"Lùi lịch hẹn cà phê với anh Tuấn lại 1 tiếng"*
  4. *"Đổi hạn nộp bài tập sang Chủ nhật tuần này"*
  5. *"Chuyển lịch đi khám răng sang 9h sáng thứ Bảy"*
  6. *"Dời lịch phỏng vấn thực tập sang tuần sau"*
  7. *"Gia hạn deadline báo cáo thêm 2 ngày"*
  8. *"Đổi giờ đi đá bóng chiều nay thành 17h30"*

---

### 2.3. `task.query_by_tag` – Lọc việc theo nhãn / Dự án
* **Mục đích:** Tra cứu danh sách các công việc thuộc một danh mục hoặc dự án chuyên biệt.
* **Đường dẫn:** **Fast Path (System 1)**.
* **Slots:**
  * `tag` (`str`, **Bắt buộc**): Tên nhãn (`"AI4Life"`, `"Đồ án tốt nghiệp"`, `"VKU"`, `"Cá nhân"`, `"Học tập"`).
* **Mẫu câu thực tế:**
  1. *"Xem các công việc thuộc dự án AI4Life"*
  2. *"Lọc danh sách việc môn Lập trình Web"*
  3. *"Có những task nào gắn nhãn Cá nhân"*
  4. *"Xem toàn bộ việc của dự án tốt nghiệp VKU"*
  5. *"Kiểm tra các việc trong nhóm Học tập"*
  6. *"Liệt kê danh sách việc gắn tag Công việc cty"*
  7. *"Xem các task liên quan đến bảo vệ đồ án"*
  8. *"Lọc các đầu việc của kỳ thi học kỳ"*

---

### 2.4. `task.query_completed` – Xem danh sách việc đã hoàn thành
* **Mục đích:** Tổng kết năng suất, xem lại những việc đã làm xong trong ngày, tuần hoặc tháng.
* **Đường dẫn:** **Fast Path (System 1)**.
* **Slots:**
  * `time_range` (`str`, Tùy chọn, fallback `"today"`): Khoảng thời gian tra cứu.
* **Mẫu câu thực tế:**
  1. *"Xem lại các việc tôi đã hoàn thành hôm nay"*
  2. *"Tuần này tôi đã làm xong được bao nhiêu task?"*
  3. *"Kiểm tra danh sách công việc đã hoàn thành trong tháng"*
  4. *"Hôm qua tôi đã tick xong những việc gì"*
  5. *"Xem tổng kết các đầu việc đã giải quyết tuần qua"*
  6. *"Cho xem lịch sử các task đã done"*
  7. *"Hôm nay đã làm được những gì rồi Onis"*
  8. *"Liệt kê việc đã hoàn tất ngày hôm qua"*

---

### 2.5. `task.cancel` – Tạm hoãn / Hủy bỏ công việc (Không xóa mất dữ liệu)
* **Mục đích:** Chuyển trạng thái task sang `cancelled`, giữ lại dữ liệu lịch sử chứ không xóa vĩnh viễn khỏi CSDL như `task.delete`.
* **Đường dẫn:** **Fast Path (System 1)**.
* **Mức độ HITL:** `None`.
* **Slots:**
  * `title` (`str`, **Bắt buộc**): Tên việc cần hủy.
  * `reason` (`str`, Tùy chọn): Lý do hủy.
* **Mẫu câu thực tế:**
  1. *"Hủy cuộc họp nhóm chiều nay do thầy bận"*
  2. *"Hủy bỏ task đi bơi tối nay"*
  3. *"Tạm hoãn việc mua sách sang tuần sau"*
  4. *"Bỏ cuộc hẹn với khách hàng chiều thứ 3"*
  5. *"Hủy lịch đá bóng vì trời mưa"*
  6. *"Hủy task đi siêu thị hôm nay"*

---

### 2.6. `task.search` – Tìm kiếm công việc theo từ khóa
* **Mục đích:** Tìm kiếm toàn văn (Full-text search) các công việc trong quá khứ hoặc hiện tại theo từ khóa người dùng nhập.
* **Đường dẫn:** **Fast Path (System 1)**.
* **Slots:**
  * `keyword` (`str`, **Bắt buộc**): Từ khóa tìm kiếm.
* **Mẫu câu thực tế:**
  1. *"Tìm các công việc có chữ slide"*
  2. *"Tìm kiếm task liên quan đến tiền điện"*
  3. *"Tìm lịch hẹn có tên anh Tuấn"*
  4. *"Tra cứu việc có từ khóa báo cáo"*
  5. *"Tìm xem tôi có ghi việc mua quà không"*
  6. *"Kiểm tra xem có task nào nhắc nộp hồ sơ không"*

---

# 🔗 3. NHÓM GIAO THOA TIỀN & VIỆC (CROSS-DOMAIN)

### 3.1. `cross.plan_expense_task` – Kế hoạch công việc gắn liền dự trù kinh phí
* **Mục đích:** Lên danh sách các việc cần chuẩn bị cho một sự kiện (du lịch, tổ chức sinh nhật, đám cưới) đồng thời dự toán kinh phí cho từng đầu việc.
* **Đường dẫn:** **Reasoning Path (System 2)** – Phối hợp giữa `TaskManagerAgent` và `FinancialAdvisoryAgent`.
* **Mức độ HITL:** `Gate 1`.
* **Slots:**
  * `event_name` (`str`, **Bắt buộc**): Tên sự kiện (`"Du lịch Đà Nẵng"`, `"Tiệc tất niên"`).
  * `budget` (`Decimal`, Tùy chọn): Ngân sách tối đa dự kiến.
  * `duration` (`str`, Tùy chọn): Thời lượng sự kiện (vd: `"3 ngày 2 đêm"`).
* **Mẫu câu thực tế:**
  1. *"Lập kế hoạch đi du lịch Đà Nẵng 3 ngày 2 đêm ngân sách 5 triệu"*
  2. *"Lên danh sách việc cần làm và dự trù chi phí tổ chức tiệc sinh nhật 2 củ"*
  3. *"Lập plan tổ chức workshop AI cho CLB với kinh phí 10 triệu"*
  4. *"Lên kế hoạch chuyển phòng trọ mới kèm dự toán chi phí vận chuyển"*
  5. *"Kế hoạch đi phượt Hà Giang và tính tiền xăng xe ăn ở"*
  6. *"Chuẩn bị kế hoạch cưới vợ và dự toán ngân sách từng hạng mục"*
  7. *"Lên danh sách mua sắm đồ Tết và giới hạn chi tiêu 8 triệu"*
  8. *"Lập bảng việc cần làm và chi phí tổ chức giải bóng đá sinh viên"*

---

### 3.2. `cross.bill_due_reminder` – Nhắc hạn đóng tiền / Hóa đơn định kỳ
* **Mục đích:** Tạo một công việc deadline thanh toán hóa đơn gắn liền với số tiền cụ thể trong sổ thu chi.
* **Đường dẫn:** **Fast Path (System 1)**.
* **Slots:**
  * `bill_name` (`str`, **Bắt buộc**): Tên khoản tiền cần nộp (tiền trọ, tiền mạng, học phí).
  * `amount` (`Decimal`, **Bắt buộc**): Số tiền cần thanh toán.
  * `due_date` (`datetime`, **Bắt buộc**): Ngày đến hạn.
* **Mẫu câu thực tế:**
  1. *"Nhắc tôi đóng tiền trọ 3tr5 vào ngày 25 hàng tháng"*
  2. *"Tạo lịch nhắc nộp học phí 12 củ trước ngày 20/11"*
  3. *"Nhắc thanh toán tiền điện 700k vào ngày mai"*
  4. *"Đặt lịch nhắc trả tiền thẻ tín dụng 4 triệu ngày 15"*
  5. *"Nhắc đóng tiền bảo hiểm xe máy 150k cuối tuần này"*
  6. *"Tạo nhắc nhở thanh toán cước internet 250k trước thứ 6"*
  7. *"Nhắc nộp tiền rác 60 nghìn đầu tháng sau"*
  8. *"Nhắc chuyển khoản tiền thuê mặt bằng 15 triệu ngày 1"*

---

# ⚙️ 4. NHÓM HỆ THỐNG & ĐIỀU KHIỂN (SYSTEM DOMAIN)

### 4.1. `system.greeting_summary` – Chào buổi sáng & Tóm tắt nhanh
* **Mục đích:** Chào hỏi đầu ngày, tổng hợp nhanh số dư khả dụng và 3 công việc quan trọng nhất cần giải quyết hôm nay.
* **Đường dẫn:** **Fast Path (System 1)**.
* **Mẫu câu thực tế:**
  1. *"Chào buổi sáng Onis"*
  2. *"Bắt đầu ngày mới tóm tắt tình hình giúp mình"*
  3. *"Good morning, hôm nay thế nào rồi"*
  4. *"Tóm tắt nhanh số dư và task hôm nay"*
  5. *"Onis ơi, chào bạn"*
  6. *"Hôm nay có gì mới không em"*
  7. *"Báo cáo đầu ngày cho tôi"*
  8. *"Chào OnisAgent, tóm tắt ngày hôm nay"*

---

### 4.2. `system.help` – Hướng dẫn sử dụng & Khả năng của Agent
* **Mục đích:** Cung cấp danh mục các câu lệnh mẫu, hướng dẫn người dùng cách ra lệnh bằng giọng nói và tương tác.
* **Đường dẫn:** **Fast Path (System 1)**.
* **Mẫu câu thực tế:**
  1. *"Bạn có thể giúp được gì cho tôi?"*
  2. *"Hướng dẫn sử dụng OnisAgent"*
  3. *"Trợ lý này làm được những việc gì"*
  4. *"Cho tôi xem các câu lệnh mẫu"*
  5. *"Làm sao để ghi chi tiêu bằng giọng nói"*
  6. *"Cách dùng app OnisAgent thế nào"*
  7. *"Trợ lý có tính được tiền lãi vay ngân hàng không"*
  8. *"Help me, hướng dẫn tính năng"*

---

### 4.3. `system.undo` – Hoàn tác thao tác vừa ghi nhận
* **Mục đích:** Hủy bỏ ngay lập tức giao dịch thu chi hoặc công việc vừa ghi nhận sai lầm ở lượt thoại trước đó.
* **Đường dẫn:** **Fast Path (System 1)**.
* **Mức độ HITL:** `Gate 2` (Đính chính giao dịch).
* **Mẫu câu thực tế:**
  1. *"Ủa nhầm rồi, hoàn tác lại giúp mình"*
  2. *"Hủy giao dịch vừa ghi nhận"*
  3. *"Tôi vừa nói nhầm, xóa khoản chi vừa rồi đi"*
  4. *"Undo lại thao tác trước đó"*
  5. *"Nhầm số tiền rồi, hủy lệnh vừa tạo"*
  6. *"Không phải task đó, hoàn tác lại"*
  7. *"Xóa khoản vừa ghi sổ đi mình đọc lộn"*
  8. *"Quay lại bước trước giúp tôi"*
