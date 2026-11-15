# OnisAgent – Danh Mục Intent & Đặc Tả Slot Chi Tiết (Intent Catalog & Slot Specification)

> **Tài liệu đặc tả chuẩn hóa Intent, Slot Schema và Chiến lược Hội thoại Làm rõ (Clarification Dialog)**  
> Thuộc hệ thống **OnisAgent Core Backend** – Tuân thủ [ADR-0004](file:///home/trinhquyetchien/Projects/Main/Team/OnisAgent/docs/adr/ADR-0004-human-in-the-loop-workflow.md) và [ADR-0006](file:///home/trinhquyetchien/Projects/Main/Team/OnisAgent/docs/adr/ADR-0006-domain-split-intent-slot-clarification.md).

---

## 📑 Bảng Tra Cứu Nhanh Danh Mục Intent (Intent Quick Reference)

| Domain | Mã Intent Chuẩn | Tên Nghiệp Vụ | Đường Dẫn Nhận Thức | Cấp Độ HITL |
| :---: | :--- | :--- | :---: | :---: |
| 💰 **Finance** | [`finance.get_balance`](#1-financeget_balance--tra-cứu-số-dư--tài-chính-hiện-tại) | Tra cứu số dư / Tài chính hiện tại | **Fast Path** (~5-12ms) | None |
| 💰 **Finance** | [`finance.add_expense`](#2-financeadd_expense--ghi-nhận-khoản-chi-tiêu) | Ghi nhận chi tiêu thường nhật | **Fast Path** (~5-12ms) | Gate 2 |
| 💰 **Finance** | [`finance.add_income`](#3-financeadd_income--ghi-nhận-khoản-thu-nhập) | Ghi nhận thu nhập | **Fast Path** (~5-12ms) | None |
| 💰 **Finance** | [`finance.budget_plan`](#4-financebudget_plan--kế-hoạch-chi-tiêu--ngân-sách) | Hạn mức chi tiêu / Ngân sách | **Reasoning Path** (Bedrock) | Gate 1 |
| 💰 **Finance** | [`finance.loan_installment_plan`](#5-financeloan_installment_plan--kế-hoạch-vay--trả-nợ-góp) | Dự toán khoản vay / Kế hoạch trả góp | **Fast Path** + **Decimal Tool** | Gate 1 |
| 💰 **Finance** | [`finance.savings_goal`](#6-financesavings_goal--quỹ-tiết-kiệm--mục-tiêu-tài-chính) | Quỹ mục tiêu tiết kiệm | **Fast Path** / **Reasoning** | Gate 1 |
| 📋 **Task** | [`task.create`](#7-taskcreate--thêm-công-việc--việc-cần-làm) | Tạo công việc / Việc cần làm | **Fast Path** (~5-12ms) | None |
| 📋 **Task** | [`task.query_today`](#8-taskquery_today--công-việc-hôm-nay) | Tra cứu công việc hôm nay / Kế hoạch ngày | **Fast Path** (~5-12ms) | None |
| 📋 **Task** | [`task.query_deadline`](#9-taskquery_deadline--tra-cứu-hạn-chót--deadline-gấp) | Cảnh báo / Tra cứu hạn chót deadline | **Fast Path** (~5-12ms) | None |
| 📋 **Task** | [`task.schedule_event`](#10-taskschedule_event--lịch-hẹn--sự-kiện) | Lên lịch hẹn / Sự kiện có mốc thời gian | **Fast Path** (~5-12ms) | None |
| 📋 **Task** | [`task.plan_schedule`](#11-taskplan_schedule--lên-kế-hoạch-tổng-thể-ngày-tuần) | Lập kế hoạch ngày/tuần (Eisenhower Matrix) | **Reasoning Path** (Bedrock) | None |
| 📋 **Task** | [`task.complete`](#12-taskcomplete--đánh-dấu-hoàn-thành-công-việc) | Đánh dấu hoàn thành việc | **Fast Path** (~5-12ms) | None |
| 📋 **Task** | [`task.delete`](#13-taskdelete--xóa--hủy-bỏ-công-việc) | Xóa công việc khỏi hệ thống | **Fast Path** (~5-12ms) | **Gate 3 (BLOCKED)** |

---

# 💰 MIỀN TÀI CHÍNH (FINANCE DOMAIN)

---

### 1. `finance.get_balance` – Tra cứu số dư / Tài chính hiện tại
* **Mục đích:** Truy vấn tức thì số dư khả dụng của từng ví cụ thể hoặc tổng hợp toàn bộ tài sản hiện có của người dùng.
* **Đường dẫn nhận thức:** **Fast Path (System 1)** – Độ trễ ~5–12ms, 0 Token LLM.
* **Mức độ HITL:** `None` (Truy vấn đọc, không làm thay đổi trạng thái dữ liệu).

#### Bảng Danh Sách Slot
| Tên Slot | Kiểu Dữ Liệu | Bắt Buộc? | Mặc Định (Fallback) | Mô Tả |
| :--- | :--- | :---: | :--- | :--- |
| `account` | `str` | Tùy chọn | `"all"` | Tên tài khoản/ví cần xem (ví dụ: `"momo"`, `"vietcombank"`, `"tiền mặt"`, `"all"`). |
| `period` | `str` | Tùy chọn | `"current"` | Mốc thời gian đối soát số dư (`"current"`, `"today"`, `"this_month"`). |

#### Chiến Lược Làm Rõ (Clarification Strategy)
* Không chặn thực thi. Nếu người dùng chỉ nói *"tôi còn bao nhiêu tiền"*, hệ thống mặc định lấy `account="all"` và tính toán tổng số dư toàn bộ các ví khả dụng.
* Nếu người dùng sở hữu $\ge 3$ tài khoản và câu lệnh mơ hồ, hiển thị Quick-Reply Chips: `["Tất cả ví", "Ví Tiền mặt", "Vietcombank", "Ví Momo"]`.

#### Mẫu Câu Huấn Luyện (Example Utterances)
1. *"Số dư hiện tại của tôi còn bao nhiêu?"*
2. *"Ví Momo còn tiền không em?"*
3. *"Tổng tài sản hiện có của anh là bao nhiêu?"*
4. *"Kiểm tra tk vietcombank còn nhiêu tiền"*
5. *"Ví tiền mặt còn bao nhiêu xị"*
6. *"Cho xem số dư tài khoản ngân hàng"*
7. *"Tài chính của tôi hôm nay thế nào"*
8. *"Check số dư khả dụng tất cả các ví"*
9. *"Tài khoản MB Bank còn bao nhiêu củ"*
10. *"Tiền tiết kiệm và tiền tiêu còn lại nhiêu z"*

---

### 2. `finance.add_expense` – Ghi nhận khoản chi tiêu
* **Mục đích:** Ghi nhận một giao dịch chi tiêu vào sổ quỹ, tự động phân loại danh mục và khấu trừ số dư chính xác bằng Python `Decimal`.
* **Đường dẫn nhận thức:** **Fast Path (System 1)** – Ghi dữ liệu tức thì.
* **Mức độ HITL:** `Gate 2` (Đính chính phân loại: Lưu vết `Correction History` nếu người dùng chỉnh sửa lại danh mục do AI gán).

#### Bảng Danh Sách Slot
| Tên Slot | Kiểu Dữ Liệu | Bắt Buộc? | Mặc Định (Fallback) | Mô Tả |
| :--- | :--- | :---: | :--- | :--- |
| `amount` | `Decimal` | **Bắt buộc** | *Không có* | Số tiền chi tiêu (> 0). Chuẩn hóa tiếng lóng (k, củ, tr, lít, xị). |
| `category` | `str` | **Bắt buộc\*** | `"Khác"` | Danh mục chi tiêu (Ăn uống, Nhà ở, Di chuyển, Mua sắm, Hóa đơn,...). |
| `note` | `str` | **Bắt buộc\*** | *Không có* | Mô tả chi tiết khoản chi. (\*Bắt buộc phải có ít nhất `category` hoặc `note`). |
| `account` | `str` | Tùy chọn | `"default_account"`| Tài khoản nguồn trừ tiền (`"tiền mặt"`, `"vcb"`,...). |
| `date` | `datetime` | Tùy chọn | `datetime.now()` | Thời điểm phát sinh chi tiêu. |
| `payment_method` | `str` | Tùy chọn | `None` | Phương thức thanh toán (`"tiền mặt"`, `"chuyển khoản"`, `"quẹt thẻ"`). |

#### Chiến Lược Làm Rõ (Clarification Strategy)
* **Khi thiếu `amount`:** Chuyển trạng thái sang `NEED_CLARIFICATION`.
  * *Câu hỏi làm rõ:* *"Bạn đã chi bao nhiêu tiền cho khoản '{note/category}' này vậy?"*
  * *Quick-Reply Chips:* `["30.000₫", "45.000₫", "100.000₫", "200.000₫"]`
* **Khi thiếu cả `category` và `note`:**
  * *Câu hỏi làm rõ:* *"Khoản tiền này bạn chi cho mục đích hoặc nội dung gì vậy?"*
  * *Quick-Reply Chips:* `["Ăn uống", "Đi lại", "Mua sắm", "Hóa đơn", "Nhà ở"]`

#### Mẫu Câu Huấn Luyện (Example Utterances)
1. *"Chi 45k trà sữa trưa nay"*
2. *"Vừa chuyển khoản 1tr5 tiền nhà cho chủ trọ"*
3. *"Đổ xăng hết 2 xị bằng tiền mặt"*
4. *"Sáng nay ăn phở bò hết 55 nghìn"*
5. *"Đóng tiền điện tháng này 780k qua VCB"*
6. *"Quẹt thẻ mua đôi giày 1tr2 ở Vincom"*
7. *"Đi siêu thị hết 850 ngàn"*
8. *"Vừa mua gói bánh 25k"*
9. *"Mới nạp card điện thoại 100k"*
10. *"Ăn lẩu với cty hết 350 cành share đôi"*

---

### 3. `finance.add_income` – Ghi nhận khoản thu nhập
* **Mục đích:** Ghi nhận dòng tiền đi vào (lương, thưởng, quà biếu, lãi đầu tư) và cộng dồn số dư ví bằng `Decimal`.
* **Đường dẫn nhận thức:** **Fast Path (System 1)**.
* **Mức độ HITL:** `None`.

#### Bảng Danh Sách Slot
| Tên Slot | Kiểu Dữ Liệu | Bắt Buộc? | Mặc Định (Fallback) | Mô Tả |
| :--- | :--- | :---: | :--- | :--- |
| `amount` | `Decimal` | **Bắt buộc** | *Không có* | Số tiền thu vào (> 0). |
| `source` | `str` | Tùy chọn | `"Thu nhập khác"` | Nguồn tiền thu về (Lương, Thưởng, Bán hàng, Bố mẹ cho,...). |
| `account` | `str` | Tùy chọn | `"default_account"`| Tài khoản đích nhận tiền. |
| `date` | `datetime` | Tùy chọn | `datetime.now()` | Thời điểm nhận tiền. |

#### Chiến Lược Làm Rõ (Clarification Strategy)
* **Khi thiếu `amount`:**
  * *Câu hỏi làm rõ:* *"Bạn đã nhận được số tiền là bao nhiêu từ '{source}'?"*
  * *Quick-Reply Chips:* `["1.000.000₫", "2.000.000₫", "5.000.000₫", "10.000.000₫"]`

#### Mẫu Câu Huấn Luyện (Example Utterances)
1. *"Nhận lương tháng 11 rồi nè 20 triệu"*
2. *"Bố gửi cho 2 củ tiêu vặt"*
3. *"Khách vừa chuyển tiền dự án freelance 5.5tr"*
4. *"Thưởng dự án AI4Life được 10 củ vào tài khoản Momo"*
5. *"Bán cái máy giặt cũ được 1tr5 tiền mặt"*
6. *"Công ty bắn thưởng quý 8 triệu rưỡi"*
7. *"Vừa nhận lại tiền nợ 500k từ thằng Nam"*
8. *"Cổ tức vừa về tài khoản 3 triệu 2"*
9. *"Mẹ cho 5 xị đi sinh nhật"*
10. *"Thu tiền nhà phòng 201 được 3 củ rưỡi"*

---

### 4. `finance.budget_plan` – Kế hoạch chi tiêu / Ngân sách
* **Mục đích:** Thiết lập hạn mức chi tiêu theo tuần/tháng, kiểm tra cảnh báo bội chi và theo dõi ngân sách cho từng danh mục.
* **Đường dẫn nhận thức:** **Reasoning Path (System 2)** – Bedrock LLM kết hợp dữ liệu dòng tiền thực tế.
* **Mức độ HITL:** `Gate 1` (Yêu cầu xác nhận áp dụng hạn mức ngân sách mới vào hệ thống).

#### Bảng Danh Sách Slot
| Tên Slot | Kiểu Dữ Liệu | Bắt Buộc? | Mặc Định (Fallback) | Mô Tả |
| :--- | :--- | :---: | :--- | :--- |
| `limit_amount` | `Decimal` | **Bắt buộc** | *Không có* | Số tiền hạn mức tối đa thiết lập. |
| `category` | `str` | Tùy chọn | `"all"` | Danh mục áp dụng hạn mức (Ăn uống, Giải trí, Mua sắm, hoặc Toàn bộ). |
| `period` | `str` | Tùy chọn | `"this_month"` | Chu kỳ ngân sách (`"this_week"`, `"this_month"`). |

#### Chiến Lược Làm Rõ (Clarification Strategy)
* **Khi thiếu `limit_amount`:**
  * *Câu hỏi làm rõ:* *"Bạn muốn đặt hạn mức ngân sách cho '{category}' là bao nhiêu tiền?"*
  * *Quick-Reply Chips:* `["2.000.000₫", "3.000.000₫", "5.000.000₫", "10.000.000₫"]`

#### Mẫu Câu Huấn Luyện (Example Utterances)
1. *"Đặt hạn mức chi tiêu tháng này 5 triệu"*
2. *"Kiểm tra ngân sách ăn uống tuần này còn bao nhiêu"*
3. *"Cài đặt ngân sách tiền ăn tháng 11 tối đa 3 củ"*
4. *"Tháng này tôi còn được tiêu bao nhiêu tiền nữa"*
5. *"Giới hạn tiền mua sắm quần áo dưới 1tr5 một tháng"*
6. *"Xem tiến độ chi tiêu theo ngân sách tuần này"*
7. *"Thiết lập hạn mức tổng chi tiêu trong tháng là 12 triệu"*
8. *"Cảnh báo khi tiền ăn uống vượt quá 80% ngân sách"*
9. *"Kiểm tra xem tuần này đã phung phí bao nhiêu phần trăm rồi"*
10. *"Lập ngân sách tiết kiệm cho sinh viên 4 triệu/tháng"*

---

### 5. `finance.loan_installment_plan` – Kế hoạch vay / Trả nợ góp
* **Mục đích:** Tính toán chính xác bảng khấu hao khoản vay theo phương thức dư nợ giảm dần, tính gốc + lãi từng tháng và kỳ cuối điều chỉnh.
* **Đường dẫn nhận thức:** **Fast Path** + **Deterministic Decimal Calculator** (AWS Lambda `calculate_loan`).
* **Mức độ HITL:** `Gate 1` (Bắt buộc người dùng nhấn xác nhận nếu muốn lưu kế hoạch trả góp vào lịch nhắc nhở).

#### Bảng Danh Sách Slot
| Tên Slot | Kiểu Dữ Liệu | Bắt Buộc? | Mặc Định (Fallback) | Mô Tả |
| :--- | :--- | :---: | :--- | :--- |
| `principal` | `Decimal` | **Bắt buộc** | *Không có* | Số tiền gốc vay (> 0). |
| `term_months` | `int` | **Bắt buộc** | *Không có* | Thời hạn trả góp tính theo tháng. |
| `annual_rate` | `Decimal` | **Bắt buộc** | *Không có* | Lãi suất theo năm (hỗ trợ nhập dạng `12%` hoặc `0.12`). |
| `method` | `str` | Tùy chọn | `"reducing_balance"`| Phương thức tính: `"reducing_balance"` (dư nợ giảm dần) hoặc `"straight_line"`. |
| `purpose` | `str` | Tùy chọn | `None` | Mục đích vay (mua xe, mua laptop, sửa nhà,...). |

#### Chiến Lược Làm Rõ (Clarification Strategy)
* **Khi thiếu `principal`:** *"Số tiền bạn dự định vay hoặc trả góp là bao nhiêu?"* $\rightarrow$ `["20.000.000₫", "50.000.000₫", "100.000.000₫"]`
* **Khi thiếu `term_months`:** *"Bạn dự định trả trong thời hạn bao nhiêu tháng?"* $\rightarrow$ `["6 tháng", "12 tháng", "24 tháng", "36 tháng"]`
* **Khi thiếu `annual_rate`:** *"Lãi suất khoản vay là bao nhiêu % một năm?"* $\rightarrow$ `["8%/năm", "10%/năm", "12%/năm", "15%/năm"]`

#### Mẫu Câu Huấn Luyện (Example Utterances)
1. *"Tính kế hoạch trả góp laptop 20 triệu trong 6 tháng lãi 12%"*
2. *"Vay mua xe 50 triệu 24 tháng lãi 10%/năm mỗi tháng trả bao nhiêu"*
3. *"Tính khoản vay mua nhà 1 tỷ trả trong 10 năm lãi 9% một năm"*
4. *"Bảng trả nợ góp 30 củ trong 12 tháng dư nợ giảm dần"*
5. *"Nếu vay 15tr trong 1 năm lãi 11% thì tháng đầu trả bao nhiêu"*
6. *"Vay ngân hàng 200 triệu kỳ hạn 36 tháng lãi suất 8.5%"*
7. *"Lập lịch trả góp điện thoại 25 củ trong 9 tháng"*
8. *"Vay tiêu dùng 40 triệu lãi 14% một năm chia 18 tháng tính sao"*
9. *"Tính tiền lãi và gốc hàng tháng cho khoản vay 80 triệu 2 năm"*
10. *"Dự toán khoản nợ xe máy 35tr trả trong 15 tháng lãi 1% tháng"*

---

### 6. `finance.savings_goal` – Quỹ tiết kiệm / Mục tiêu tài chính
* **Mục đích:** Khởi tạo quỹ tích lũy mục tiêu, tính toán số tiền cần gửi định kỳ mỗi tháng để đạt mục tiêu đúng hạn.
* **Đường dẫn nhận thức:** **Fast Path (System 1)** cho khởi tạo nhanh; **Reasoning Path** khi yêu cầu cố vấn chiến lược tích lũy.
* **Mức độ HITL:** `Gate 1` (Xác nhận cam kết tạo quỹ mới vào DynamoDB).

#### Bảng Danh Sách Slot
| Tên Slot | Kiểu Dữ Liệu | Bắt Buộc? | Mặc Định (Fallback) | Mô Tả |
| :--- | :--- | :---: | :--- | :--- |
| `goal_name` | `str` | **Bắt buộc** | *Không có* | Tên quỹ hoặc mục đích tiết kiệm. |
| `target_amount` | `Decimal` | **Bắt buộc** | *Không có* | Số tiền mục tiêu cần đạt (> 0). |
| `deadline` | `datetime` | Tùy chọn | `None` | Mốc thời gian hoàn thành mục tiêu. |
| `monthly_contribution` | `Decimal` | Tùy chọn | `None` | Số tiền dự kiến tích lũy mỗi tháng. |

#### Chiến Lược Làm Rõ (Clarification Strategy)
* **Khi thiếu `goal_name`:** *"Mục tiêu hoặc tên quỹ tiết kiệm của bạn là gì?"* $\rightarrow$ `["Quỹ khẩn cấp", "Mua xe mới", "Du lịch Nhật", "Mua laptop"]`
* **Khi thiếu `target_amount`:** *"Bạn muốn tích lũy số tiền bao nhiêu cho mục tiêu '{goal_name}'?"* $\rightarrow$ `["10.000.000₫", "20.000.000₫", "50.000.000₫", "100.000.000₫"]`

#### Mẫu Câu Huấn Luyện (Example Utterances)
1. *"Tạo quỹ tiết kiệm mua xe 50 triệu trước Tết"*
2. *"Đã gửi vào tiết kiệm 2 củ mua laptop"*
3. *"Tôi muốn để dành 100 củ đi du lịch Nhật cuối năm sau"*
4. *"Lập quỹ khẩn cấp 6 tháng chi tiêu 40 triệu"*
5. *"Mục tiêu tiết kiệm 15 triệu mua iPhone mới"*
6. *"Tạo hũ tiết kiệm cưới vợ 200 triệu hạn 2 năm"*
7. *"Thêm quỹ tích lũy học phí học kỳ sau 12 củ"*
8. *"Xem tiến độ các quỹ tiết kiệm hiện có"*
9. *"Để dành mỗi tháng 3 triệu để mua vàng"*
10. *"Mở quỹ tiết kiệm mua máy tính 30tr trong 8 tháng"*

---

# 📋 MIỀN CÔNG VIỆC & THỜI GIAN (TASK & SCHEDULE DOMAIN)

---

### 7. `task.create` – Thêm công việc / Việc cần làm
* **Mục đích:** Thêm nhanh một công việc cần làm vào danh sách nhiệm vụ cá nhân, phân loại ưu tiên và gắn nhãn dự án.
* **Đường dẫn nhận thức:** **Fast Path (System 1)** – Phản xạ tức thì ~5–12ms.
* **Mức độ HITL:** `None`.

#### Bảng Danh Sách Slot
| Tên Slot | Kiểu Dữ Liệu | Bắt Buộc? | Mặc Định (Fallback) | Mô Tả |
| :--- | :--- | :---: | :--- | :--- |
| `title` | `str` | **Bắt buộc** | *Không có* | Tiêu đề hoặc nội dung việc cần làm. |
| `deadline` | `datetime` | Tùy chọn | `None` | Hạn chót công việc (ngày & giờ). |
| `priority` | `TaskPriority`| Tùy chọn | `TaskPriority.MEDIUM`| Mức ưu tiên (`"low"`, `"medium"`, `"high"`, `"urgent"`). |
| `category` | `str` | Tùy chọn | `"Chung"` | Phân loại dự án/nhóm việc (Học tập, VKU, Công ty, Cá nhân,...). |
| `reminder` | `bool` | Tùy chọn | `False` | Có bật chuông/thông báo đẩy nhắc nhở không. |

#### Chiến Lược Làm Rõ (Clarification Strategy)
* **Khi thiếu `title`:**
  * *Câu hỏi làm rõ:* *"Nội dung công việc hoặc việc bạn cần làm là gì?"*
  * *Quick-Reply Chips:* `["Nộp bài tập", "Gửi email cho sếp", "Đi chợ", "Họp nhóm"]`
* **Khi chưa có `deadline` (Hỏi nhẹ - Soft prompt):**
  * Tự động lưu task với `deadline=None`, đồng thời kèm thông báo: *"Đã tạo task '{title}'. Bạn có muốn gắn thêm hạn chót không?"* $\rightarrow$ `["Hôm nay 18:00", "Ngày mai", "Cuối tuần này"]`.

#### Mẫu Câu Huấn Luyện (Example Utterances)
1. *"Thêm việc nộp báo cáo AI4Life trước 5h chiều mai"*
2. *"Nhắc tôi mua sữa cho con chiều nay"*
3. *"Tạo task chuẩn bị slide thuyết trình VKU"*
4. *"Ghi chú việc gọi điện cho khách hàng lúc 9h sáng thứ 2"*
5. *"Thêm công việc sửa lỗi backend OnisAgent gấp"*
6. *"Nhắc anh đi tập gym lúc 19h tối nay"*
7. *"Tạo nhiệm vụ đọc 2 chương sách chuyên ngành"*
8. *"Ghi lại việc mua quà sinh nhật cho mẹ cuối tuần"*
9. *"Nhắc tôi nộp tiền mạng trước ngày 20"*
10. *"Tạo task gửi tài liệu nghiệm thu cho thầy hướng dẫn"*

---

### 8. `task.query_today` – Công việc hôm nay / Kế hoạch ngày
* **Mục đích:** Liệt kê toàn bộ công việc, nhiệm vụ và sự kiện cần hoàn tất trong ngày hôm nay kèm trạng thái hoàn thành.
* **Đường dẫn nhận thức:** **Fast Path (System 1)**.
* **Mức độ HITL:** `None`.

#### Bảng Danh Sách Slot
| Tên Slot | Kiểu Dữ Liệu | Bắt Buộc? | Mặc Định (Fallback) | Mô Tả |
| :--- | :--- | :---: | :--- | :--- |
| `date_filter` | `str` | Tùy chọn | `"today"` | Mốc lọc ngày (`"today"`, `"current_day"`). |
| `status` | `str` | Tùy chọn | `"pending"` | Trạng thái việc (`"all"`, `"pending"`, `"completed"`). |

#### Chiến Lược Làm Rõ (Clarification Strategy)
* Luôn tự động thực thi ngay lập tức. Không yêu cầu người dùng cung cấp thêm slot.

#### Mẫu Câu Huấn Luyện (Example Utterances)
1. *"Hôm nay tôi có những việc gì cần làm?"*
2. *"Lên danh sách việc hôm nay"*
3. *"Xem task ngày hôm nay của tôi"*
4. *"Hôm nay có việc gì gấp không Onis"*
5. *"Lịch làm việc hôm nay thế nào"*
6. *"Cho tôi xem các đầu việc cần giải quyết hôm nay"*
7. *"Hôm nay còn việc nào chưa hoàn thành"*
8. *"Danh sách to-do list hôm nay"*
9. *"Check task ngày 15/11 giúp mình"*
10. *"Xem tổng hợp công việc ngày hôm nay"*

---

### 9. `task.query_deadline` – Tra cứu hạn chót / Deadline gấp
* **Mục đích:** Rà soát và cảnh báo các mốc deadline quan trọng sắp đến hạn trong vòng 24–72 giờ tới, đếm ngược thời gian còn lại.
* **Đường dẫn nhận thức:** **Fast Path (System 1)**.
* **Mức độ HITL:** `None`.

#### Bảng Danh Sách Slot
| Tên Slot | Kiểu Dữ Liệu | Bắt Buộc? | Mặc Định (Fallback) | Mô Tả |
| :--- | :--- | :---: | :--- | :--- |
| `time_range` | `str` | Tùy chọn | `"upcoming_48h"`| Khoảng thời gian tra cứu (`"today"`, `"this_week"`, `"all"`). |
| `urgency_only`| `bool`| Tùy chọn | `False` | Chỉ lọc những task thuộc mức khẩn cấp (`urgent` / `high`). |

#### Chiến Lược Làm Rõ (Clarification Strategy)
* Tự động quét toàn bộ task có `deadline != None` và sắp xếp theo thứ tự thời gian tăng dần.

#### Mẫu Câu Huấn Luyện (Example Utterances)
1. *"Tuần này có deadline nào gấp không?"*
2. *"Hạn nộp đồ án VKU là khi nào?"*
3. *"Kiểm tra các deadline sắp tới trong 3 ngày tới"*
4. *"Có bài tập nào sắp hết hạn nộp không"*
5. *"Xem những hạn chót cần làm gấp trong 24h tới"*
6. *"Deadline bài báo khoa học còn bao nhiêu tiếng nữa"*
7. *"Liệt kê các hạn chót chưa xong trong tuần này"*
8. *"Khi nào tới hạn nộp slide thuyết trình"*
9. *"Check xem có việc nào sắp quá hạn không em"*
10. *"Thời hạn đóng học phí là ngày mấy thế"*

---

### 10. `task.schedule_event` – Lịch hẹn / Sự kiện
* **Mục đích:** Ghi nhận cuộc hẹn, cuộc họp nhóm, sự kiện ngoại khóa có thời gian bắt đầu và địa điểm cụ thể.
* **Đường dẫn nhận thức:** **Fast Path (System 1)**.
* **Mức độ HITL:** `None`.

#### Bảng Danh Sách Slot
| Tên Slot | Kiểu Dữ Liệu | Bắt Buộc? | Mặc Định (Fallback) | Mô Tả |
| :--- | :--- | :---: | :--- | :--- |
| `title` | `str` | **Bắt buộc** | *Không có* | Tiêu đề cuộc hẹn hoặc sự kiện. |
| `start_time` | `datetime` | **Bắt buộc** | *Không có* | Thời gian bắt đầu cuộc hẹn. |
| `location` | `str` | Tùy chọn | `None` | Địa điểm diễn ra (Google Meet, Highlands, VKU,...). |
| `participants`| `list[str]`| Tùy chọn | `[]` | Người tham gia cùng. |

#### Chiến Lược Làm Rõ (Clarification Strategy)
* **Khi thiếu `start_time`:**
  * *Câu hỏi làm rõ:* *"Sự kiện '{title}' diễn ra vào thời gian nào vậy bạn?"*
  * *Quick-Reply Chips:* `["9h sáng mai", "14h chiều nay", "8h tối nay", "9h sáng thứ Hai"]`

#### Mẫu Câu Huấn Luyện (Example Utterances)
1. *"Đặt lịch hẹn cà phê với anh Tuấn 9h sáng mai"*
2. *"Lịch họp nhóm lúc 2h chiều thứ 2 tại phòng Lab"*
3. *"Hẹn gặp thầy hướng dẫn lúc 15h30 chiều thứ 5 ở VKU"*
4. *"Lên lịch phỏng vấn thực tập 10h sáng thứ Sáu qua Google Meet"*
5. *"Hẹn ăn tối với đối tác 19h tối mốt tại Pizza 4P"*
6. *"Thêm lịch họp online lúc 20h tối nay"*
7. *"Đặt lịch khám răng lúc 8h sáng Chủ nhật"*
8. *"Ghi lịch bảo vệ đồ án tốt nghiệp sáng 25/11"*
9. *"Chiều nay 16h có hẹn đá bóng với công ty"*
10. *"Họp ban chủ nhiệm CLB AI lúc 17h thứ 4 tuần sau"*

---

### 11. `task.plan_schedule` – Lên kế hoạch tổng thể (Ngày / Tuần)
* **Mục đích:** Sử dụng mô hình tư duy sâu (Reasoning Path) để phân tích khối lượng công việc, sắp xếp lịch trình tối ưu theo ma trận Eisenhower và cân đối thời gian biểu.
* **Đường dẫn nhận thức:** **Reasoning Path (System 2)** – Điều phối bởi `TaskManagerAgent` qua Amazon Bedrock.
* **Mức độ HITL:** `None` (Đưa ra bảng đề xuất thời gian biểu cho người dùng tham khảo).

#### Bảng Danh Sách Slot
| Tên Slot | Kiểu Dữ Liệu | Bắt Buộc? | Mặc Định (Fallback) | Mô Tả |
| :--- | :--- | :---: | :--- | :--- |
| `time_frame` | `str` | Tùy chọn | `"today"` | Khung thời gian lập kế hoạch (`"today"`, `"tomorrow"`, `"next_week"`). |
| `focus_goal` | `str` | Tùy chọn | `None` | Mục tiêu trọng tâm cần ưu tiên hoàn thành trước. |

#### Chiến Lược Làm Rõ (Clarification Strategy)
* Không chặn thực thi. Agent tự động truy vấn toàn bộ task đang `pending` trong database, tổng hợp mức độ khẩn cấp và sinh ra thời gian biểu khuyến nghị.

#### Mẫu Câu Huấn Luyện (Example Utterances)
1. *"Lên kế hoạch công việc cho tuần tới giúp mình"*
2. *"Sắp xếp thứ tự ưu tiên các việc hôm nay theo ma trận Eisenhower"*
3. *"Lập lịch trình làm việc ngày mai sao cho hiệu quả nhất"*
4. *"Tối ưu hóa thời gian biểu tuần này để kịp nộp đồ án"*
5. *"Hôm nay có nhiều task quá, nên làm việc gì trước"*
6. *"Phân bổ thời gian học tập và làm việc cho ngày thứ 7"*
7. *"Lập kế hoạch ôn thi tuần tới cho 3 môn chuyên ngành"*
8. *"Giúp mình sắp xếp lịch làm việc hôm nay để không bị trễ deadline"*
9. *"Gợi ý thời gian biểu cho ngày mai từ 8h sáng đến 18h"*
10. *"Kế hoạch hành động tuần này để đạt mục tiêu hoàn thành đồ án"*

---

### 12. `task.complete` – Đánh dấu hoàn thành công việc
* **Mục đích:** Cập nhật trạng thái một công việc sang `isCompleted = True`, ghi nhận thời gian hoàn tất.
* **Đường dẫn nhận thức:** **Fast Path (System 1)**.
* **Mức độ HITL:** `None`.

#### Bảng Danh Sách Slot
| Tên Slot | Kiểu Dữ Liệu | Bắt Buộc? | Mặc Định (Fallback) | Mô Tả |
| :--- | :--- | :---: | :--- | :--- |
| `title` | `str` | **Bắt buộc\*** | *Không có* | Tiêu đề công việc cần hoàn thành. |
| `task_id` | `str` | **Bắt buộc\*** | *Không có* | ID định danh công việc (\*Phải có ít nhất `title` hoặc `task_id`). |
| `completion_date`| `datetime` | Tùy chọn | `datetime.now()` | Thời điểm hoàn thành. |

#### Chiến Lược Làm Rõ (Clarification Strategy)
* **Khi nói chung chung (vd: *"xong việc rồi"*):**
  * *Câu hỏi làm rõ:* *"Bạn muốn đánh dấu hoàn thành công việc nào trong danh sách dưới đây?"*
  * *Quick-Reply Chips:* Danh sách 3-4 task đang `pending` gần nhất.

#### Mẫu Câu Huấn Luyện (Example Utterances)
1. *"Xong task báo cáo AI rồi nè"*
2. *"Đánh dấu hoàn thành việc đặt vé máy bay giúp mình"*
3. *"Đã làm xong bài tập lập trình Java"*
4. *"Tick hoàn thành task nộp tiền điện"*
5. *"Hoàn tất việc gửi mail cho khách hàng rồi"*
6. *"Việc mua sữa đã làm xong nhé"*
7. *"Check done task chuẩn bị slide"*
8. *"Vừa họp nhóm xong, tick hoàn thành giùm"*
9. *"Đã hoàn thành công việc đi siêu thị"*
10. *"Xong hết việc hôm nay rồi"*

---

### 13. `task.delete` – Xóa / Hủy bỏ công việc
* **Mục đích:** Xóa một hoặc nhiều nhiệm vụ khỏi danh sách. Đây là thao tác có nguy cơ phá hủy dữ liệu.
* **Đường dẫn nhận thức:** **Fast Path (System 1)** $\longrightarrow$ **Chuyển sang trạng thái `BLOCKED`**.
* **Mức độ HITL:** **Gate 3 (Bắt buộc xác nhận trực tiếp)**. Hệ thống không bao giờ tự ý xóa nếu người dùng chưa bấm xác nhận hoặc gõ chữ đồng ý.

#### Bảng Danh Sách Slot
| Tên Slot | Kiểu Dữ Liệu | Bắt Buộc? | Mặc Định (Fallback) | Mô Tả |
| :--- | :--- | :---: | :--- | :--- |
| `title` | `str` | **Bắt buộc\*** | *Không có* | Tên công việc muốn xóa. |
| `task_id` | `str` | **Bắt buộc\*** | *Không có* | ID công việc muốn xóa. |
| `requires_hitl`| `bool`| Tự động gán | `True` | Cờ bảo mật kích hoạt Modal cảnh báo đỏ. |

#### Chiến Lược Làm Rõ & Xác Nhận (HITL Confirmation Dialog)
* **Khi xác định được task cần xóa:**
  * Trả về: `ExecutionStatus.BLOCKED`
  * *Cảnh báo UI:* *"Xác nhận xóa: Bạn có chắc chắn muốn xóa vĩnh viễn công việc '{title}' không?"*
  * *Nút bấm hành động:* `[Hủy bỏ]`, `[Xác nhận xóa]`

#### Mẫu Câu Huấn Luyện (Example Utterances)
1. *"Xóa task đi chợ chiều nay"*
2. *"Hủy việc họp nhóm với bên marketing"*
3. *"Xóa bỏ công việc nộp báo cáo cũ"*
4. *"Bỏ task đặt vé xe đi không cần nữa"*
5. *"Xóa nhiệm vụ đi xem phim tối nay"*
6. *"Hủy lịch hẹn cà phê ngày mai"*
7. *"Delete task sửa lỗi giao diện"*
8. *"Bỏ công việc kiểm tra mail buổi sáng"*
9. *"Xóa task có id 1731635892"*
10. *"Hủy toàn bộ việc đã lên lịch hôm nay"*

---

## 🛡️ Tích Hợp Vào Engine & Flutter App

1. **Backend Validation:** Mọi Intent trên đều được ánh xạ 1:1 qua `backend/src/schemas/finance.py`, `backend/src/schemas/task.py` và kiểm tra hợp lệ bởi `backend/src/engine/slot_validator.py`.
2. **Session Persistence:** Quá trình hội thoại làm rõ được duy trì trạng thái phiên đa lượt thông qua `backend/src/engine/session_manager.py`.
3. **Frontend Interaction:** Ứng dụng Flutter hiển thị thẻ câu hỏi tự nhiên cùng dãy nút `Quick-Reply Chips` giúp người dùng phản hồi nhanh chỉ bằng 1 cú chạm.
