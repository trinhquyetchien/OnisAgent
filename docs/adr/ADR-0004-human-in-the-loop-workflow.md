---
id: ADR-0004
timestamp: 2026-10-10T00:00:00Z
status: accepted
deciders: Trịnh Quyết Chiến, Hứa Huỳnh Anh
tags:
  - onisagent
  - hitl
  - human-in-the-loop
  - guardrails
  - security
  - compliance
  - user-approval
  - trigger-gates
  - loan-approval
  - savings-goals
  - re-classification
  - write-high
related_adrs: [ADR-0001, ADR-0002, ADR-0003, ADR-0005]
---

# ADR-0004: Thiết Lập Cơ Chế Kiểm Soát Người Dùng (Human-in-the-Loop) & 3 Chốt Phê Duyệt An Toàn (Trigger Gates)

> **Y-Statement:** Trong ngữ cảnh OnisAgent ứng dụng kiến trúc Dual-Path kết hợp Multi-Agent Swarm để tự động phân loại giao dịch, dự toán khoản vay trả góp dư nợ giảm dần, khởi tạo quỹ tiết kiệm và sắp xếp công việc, đối mặt với rủi ro sai lệch tự nhiên của AI và yêu cầu bảo vệ tuyệt đối dữ liệu tài chính/công việc cá nhân, chúng tôi quyết định thiết lập **Cơ chế Kiểm soát Người dùng (Human-in-the-Loop - HITL)** theo triết lý **"AI đề xuất, Người dùng quyết định" (AI Proposes, Human Disposes)** thông qua **3 Chốt Phê Duyệt An Toàn (Trigger Gates)** cụ thể:
> 1. **Gate 1 - Khởi tạo Khoản Vay hoặc Quỹ Tiết Kiệm Mới:** Bắt buộc người dùng bấm xác nhận trực tiếp trước khi áp dụng lịch trả góp khoản vay dư nợ giảm dần hoặc khởi tạo mục tiêu tiết kiệm mới vào DynamoDB.
> 2. **Gate 2 - Đính Chính Phân Loại (Re-classification):** Thu thập và lưu vết `Correction History` được phân vùng cách ly theo `user_id` mỗi khi người dùng sửa đổi danh mục thu chi để cá nhân hóa và hoàn thiện đề xuất tương lai.
> 3. **Gate 3 - Thao Tác Rủi Ro Cao (`write_high`):** Chặn thực thi tự động và yêu cầu xác nhận trực tiếp đối với hành vi sửa đổi số dư ban đầu hoặc xóa task hàng loạt,
> chấp nhận sự đánh đổi về việc tăng thêm một bước xác nhận (friction) trên giao diện đối với các hành động có mức độ ảnh hưởng lớn để đổi lấy sự an toàn và minh bạch dữ liệu tuyệt đối.

---

### 1. Problem Statement & Architectural Intent (Bài toán & Ý tưởng Kiến trúc)

**Bài toán (Context):**
Trong các hệ sinh thái AI Agent tự chủ (Autonomous Agents), khi mô hình được trao quyền ghi hoặc xóa trực tiếp vào CSDL tài chính và nhiệm vụ cá nhân mà không có sự kiểm soát của con người, hệ thống sẽ gặp các rủi ro nguy hiểm:
1. **Tự ý kích hoạt nghĩa vụ tài chính dài hạn:** Agent tự động cam kết một kế hoạch trả góp khoản vay nhiều năm hoặc tự ý tạo quỹ tiết kiệm định kỳ dựa trên một suy luận chưa hoàn chỉnh, làm phát sinh cam kết tài chính ngoài ý muốn của người dùng.
2. **Sai lệch danh mục tích tụ (Misclassification Drift):** Khi AI phân loại sai danh mục (ví dụ gán hóa đơn tiền điện vào "Giải trí"), nếu người dùng không được phản hồi hoặc sửa chữa, các báo cáo tài chính lũy kế và phân tích dòng tiền sẽ bị sai lệch nghiêm trọng.
3. **Thao tác phá hủy không thể phục hồi (Destructive Actions):** Người dùng vô tình ra lệnh giọng nói mơ hồ (ví dụ: *"Dọn dẹp công việc"* hoặc *"Đặt lại tiền"*), Agent có thể hiểu nhầm thành lệnh xóa toàn bộ nhiệm vụ hoặc ghi đè số dư ban đầu, dẫn đến mất mát dữ liệu nghiêm trọng.

**Mục đích kiến trúc (Intent):**
Thiết lập nguyên tắc **"AI Proposes, Human Disposes"**: AI Agent chỉ đóng vai trò phân tích, tham mưu và soạn thảo đề xuất (Drafting/Proposing); toàn bộ quyền quyết định ghi nhận vĩnh viễn (Committing) vào CSDL thuộc về người dùng. Quy trình này được thể chế hóa thông qua **3 Chốt Phê Duyệt An Toàn (3 Trigger Gates)** được thực thi tại tầng Policy Engine và giao diện người dùng.

---

### 2. Đặc Tả Chi Tiết 3 Chốt Phê Duyệt An Toàn (3 Trigger Gates)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        3 CHỐT KIỂM SOÁT AN TOÀN (TRIGGER GATES)                        │
├─────────────────────┬───────────────────────────┬──────────────────────────────────────┤
│ Chốt Kiểm Soát      │ Điều Kiện Kích Hoạt       │ Cơ Chế Xử Lý & Ràng Buộc             │
├─────────────────────┼───────────────────────────┼──────────────────────────────────────┤
│ Gate 1: Xác Nhận Áp │ • FinancialAdvisoryAgent  │ • Trạng thái: Pending Approval State │
│ Dụng Lịch Trả Góp   │   dự toán lịch trả góp    │ • Giao diện: Hiển thị bảng chi tiết  │
│ Khoản Vay hoặc Quỹ  │   khoản vay hoặc mục tiêu │   gốc, lãi, kỳ hạn, tiến độ          │
│ Tiết Kiệm Mới       │   tiết kiệm mới           │ • Bắt buộc bấm "Xác nhận áp dụng"    │
├─────────────────────┼───────────────────────────┼──────────────────────────────────────┤
│ Gate 2: Đính Chính  │ • Người dùng chỉnh sửa    │ • Cập nhật danh mục mới vào DB       │
│ Phân Loại Thu Chi   │   danh mục giao dịch do   │ • Lưu vết vào Correction History     │
│ (Re-classification) │   AI đề xuất              │ • Cô lập tuyệt đối theo user_id      │
│                     │                           │ • Dùng làm Few-shot cá nhân hóa      │
├─────────────────────┼───────────────────────────┼──────────────────────────────────────┤
│ Gate 3: Thao Tác    │ • Policy Engine phát hiện │ • Decision Router gán nhãn BLOCKED   │
│ Rủi Ro Cao          │   hành vi phá hủy:        │ • Kích hoạt Modal Cảnh báo Đỏ        │
│ (write_high)        │   - Thay đổi số dư ban đầu│ • Yêu cầu người dùng bấm xác nhận    │
│                     │   - Xóa task hàng loạt    │   hoặc gõ chữ xác nhận trực tiếp     │
└─────────────────────┴───────────────────────────┴──────────────────────────────────────┘
```

#### 2.1. Gate 1 - Xác Nhận Áp Dụng Lịch Trả Góp Khoản Vay hoặc Quỹ Tiết Kiệm Mới (Loan Schedule & Savings Goal Gate)
- **Kịch bản:** Khi `FinancialAdvisoryAgent` hoàn thành tính toán dự toán khoản vay trả góp dư nợ giảm dần bằng Python `Decimal` (Ví dụ: vay 50 triệu trong 12 tháng lãi 10%/năm, mỗi tháng trả 4.395.794 đ) hoặc đề xuất một mục tiêu tiết kiệm mới (Ví dụ: *"Quỹ mua laptop 35 triệu"*).
- **Cơ chế kiểm soát:**
  1. Hệ thống chuyển sang trạng thái chờ phê duyệt `Pending Approval State`.
  2. Giao diện (Streamlit/Web Dashboard) dựng thẻ trực quan hiển thị đầy đủ bảng lịch trả góp gốc + lãi từng tháng hoặc mục tiêu tiết kiệm kèm thanh tiến độ dự kiến.
  3. Chỉ khi người dùng chủ động bấm vào nút **[Xác nhận áp dụng]**, API mới thực hiện ghi nhận bản ghi vào bảng `SavingsGoals` hoặc lịch trình nợ trong CSDL DynamoDB.
  4. Nếu người dùng bấm **[Hủy bỏ]** hoặc phớt lờ, không có dữ liệu tài chính ràng buộc nào được ghi vào cơ sở dữ liệu.

#### 2.2. Gate 2 - Đính Chính Phân Loại & Lưu Vết Lịch Sử Sửa Đổi (Re-classification & Correction Gate)
- **Kịch bản:** Khi `CategorizationAgent` tự động gán nhãn một giao dịch (ví dụ: gán hóa đơn ăn uống ngoài giờ vào "Khác"), nhưng người dùng muốn đổi thành "Ăn uống".
- **Cơ chế kiểm soát:**
  1. Người dùng chọn lại danh mục đúng thông qua Dropdown trên UI hoặc ra lệnh giọng nói (*"Đổi giao dịch phở sang ăn uống"*).
  2. Giao diện cập nhật lại danh mục giao dịch trong bảng `Transactions`.
  3. **Lưu vết Correction History:** Hệ thống tự động ghi nhận một bản ghi hiệu chỉnh gồm:
     ```json
     {
       "user_id": "usr_9823",
       "tx_id": "tx_1792348",
       "raw_description": "Ăn bát phở sáng 45k",
       "ai_predicted_category": "Khác",
       "user_corrected_category": "Ăn uống",
       "timestamp": "2026-10-15T14:30:00Z"
     }
     ```
  4. **Quy tắc phân vùng (Partitioning Rule):** Toàn bộ `Correction History` được phân vùng và mã hóa độc quyền theo `user_id`, tuyệt đối **không chia sẻ chéo tenant (Cross-tenant Isolation)**. Dữ liệu này chỉ được dùng làm Few-shot Context để cải thiện độ chính xác phân loại của chính người dùng đó trong tương lai.

#### 2.3. Gate 3 - Thao Tác Rủi Ro Cao (`write_high` / Destructive Action Gate)
- **Kịch bản:** Người dùng yêu cầu hoặc AI nhận diện các tác vụ có tính phá hủy hoặc tác động tài chính cốt lõi:
  - Thay đổi hoặc ghi đè số dư tiền mặt ban đầu (`balance.override`).
  - Xóa nhiệm vụ hàng loạt (`task.bulk_delete`).
  - Xóa toàn bộ lịch sử thu chi một giai đoạn.
- **Cơ chế kiểm soát:**
  1. Policy Engine phân tích ý định và lập tức đánh dấu mức độ rủi ro: `Risk = 'write_high'`.
  2. Decision Router lập tức chặn đứng việc thực thi tự động (Blocked Path): Tuyệt đối không truyền lệnh xuống CSDL.
  3. Giao diện kích hoạt **Modal Cảnh báo Đỏ (Red Alert Modal)** với cơ chế xác nhận 2 bước:
     - Hiển thị rõ danh sách các mục sắp bị xóa hoặc số dư ban đầu sắp bị thay đổi.
     - Yêu cầu người dùng bấm nút nguy hiểm có đếm ngược hoặc gõ chữ xác nhận *"XÁC NHẬN"* trước khi lệnh ghi xuống DB được giải phóng.

---

### 3. Options Considered & Rejection Reasons (Các phương án & Lý do bác bỏ)

| Phương án | Ưu điểm (Pros) | Nhược điểm (Cons) | Lý do bác bỏ / lựa chọn |
|---|---|---|---|
| **Option A: Full Autonomy (Tự động hoàn toàn 100%)** | Tốc độ nhanh; người dùng không cần bấm xác nhận. | Cực kỳ nguy hiểm; AI tự ý cam kết khoản vay hoặc xóa nhầm task; không thể hoàn tác nếu không có bản sao lưu. | **BÁC BỎ:** Hoàn toàn không chấp nhận được đối với ứng dụng quản lý tài chính cá nhân. |
| **Option B: Passive Logging Only (Chỉ ghi log kiểm toán sau khi đã thực thi)** | Không làm gián đoạn người dùng; có lịch sử để tra cứu lại. | Lỗi sai đã xảy ra trên CSDL; người dùng phải mất công sức dò tìm và khắc phục hậu quả. | **BÁC BỎ:** Chỉ mang tính chất "chữa cháy", không bảo vệ chủ động người dùng trước các quyết định sai lầm của AI. |
| **Option C: Interactive HITL 3 Trigger Gates** | Minh bạch 100%; người dùng nắm toàn quyền kiểm soát; phân loại rủi ro thông minh; học hỏi từ lịch sử đính chính. | Tăng thêm 1 bước tương tác (friction) đối với các hành động rủi ro cao. | **ĐƯỢC CHỌN:** Sự cân bằng tối ưu giữa tính tiện lợi của AI và sự an toàn tuyệt đối của người dùng. |

---

### 4. Directives & Rules (Quy định bắt buộc)

- **MUST NOT (Cấm tự động ghi nợ/tiết kiệm):** Codebase MUST NOT tự động cập nhật lịch trả góp khoản vay hoặc mục tiêu tiết kiệm mới nếu người dùng chưa bấm nút xác nhận chấp thuận đề xuất (Gate 1).
- **MUST (Lưu trữ Correction History phân vùng):** Mọi thao tác sửa danh mục từ người dùng (Gate 2) MUST được ghi nhận vào `Correction History` và phân vùng nghiêm ngặt theo `user_id`. Không được chia sẻ dữ liệu hiệu chỉnh sang profile của người dùng khác.
- **MUST (Chặn đứng thao tác write_high):** Khi ý định được Policy Engine phân loại là `write_high` (Gate 3 - sửa số dư ban đầu, xóa task hàng loạt), hệ thống MUST chặn thực thi ngầm và MUST yêu cầu xác nhận rõ ràng từ UI trước khi gửi lệnh tới tầng Database.
- **MUST (Idempotency Key):** Các lệnh gửi xác nhận từ HITL Approval Gates MUST sử dụng khóa bất biến (Idempotency Key) để ngăn chặn việc người dùng double-click gây lặp lại giao dịch hoặc tạo trùng mục tiêu tiết kiệm.
- **MUST (Bảo toàn ADR-0001):** Số liệu tài chính hiển thị trên các màn hình phê duyệt HITL MUST được tính toán bằng Python `Decimal`, không dựa trên số học do LLM tự bịa ra.

---

### 5. Consequences & Acceptance Criteria (Hệ quả & Tiêu chuẩn nghiệm thu)

#### A. Lợi ích đạt được
- **Loại bỏ rủi ro phá hủy dữ liệu:** Ngăn chặn 100% tình trạng mất mát dữ liệu do AI hiểu sai lệnh xóa hoặc ghi đè số dư ban đầu.
- **Minh bạch & Làm chủ tài chính:** Người dùng luôn là người ra quyết định cuối cùng đối với kế hoạch vay vốn và mục tiêu tiết kiệm của chính mình.
- **Tự hoàn thiện thông minh:** Hệ thống ngày càng phân loại chính xác hơn nhờ tận dụng tập dữ liệu hiệu chỉnh cá nhân hóa trong `Correction History`.

#### B. Đánh đổi & Thách thức
- Người dùng phải thực hiện thêm 1 thao tác nhấn chuột khi áp dụng khoản vay, tiết kiệm hoặc thực hiện thao tác xóa nhạy cảm.
- Cần quản lý trạng thái chờ duyệt (`st.session_state` hoặc backend approval token) một cách chặt chẽ.

#### C. Tiêu chuẩn nghiệm thu (Acceptance Criteria)
1. **Kiểm thử Gate 1 (Khoản vay & Tiết kiệm):** Đề xuất lịch trả góp khoản vay hoặc mục tiêu tiết kiệm từ Agent không làm thay đổi dữ liệu trong CSDL cho đến khi nhận được sự kiện `approve_plan_clicked`.
2. **Kiểm thử Gate 2 (Đính chính):** Sửa danh mục giao dịch thành công, bản ghi `Correction History` xuất hiện trong CSDL với đúng `user_id`, và lần phân loại tiếp theo cho từ khóa tương tự ưu tiên danh mục mới.
3. **Kiểm thử Gate 3 (write_high):** Lệnh sửa số dư ban đầu hoặc xóa task hàng loạt bị chặn tự động ở tầng Policy Engine; chỉ thực thi khi payload gửi lên đi kèm cờ `user_confirmed: true`.
4. **Cô lập Tenant:** Kiểm thử xác nhận người dùng B không bao giờ đọc được hoặc bị ảnh hưởng bởi `Correction History` của người dùng A.

---

### 6. Revisit Triggers (Điều kiện xem xét lại)

Cần đánh giá lại quyết định kiến trúc này khi:
1. Độ tin cậy phân loại của Agent đạt $\ge 98\%$ liên tục qua 500 giao dịch của cùng 1 người dùng, có thể cân nhắc tùy chọn người dùng tự bật chế độ "Tự động duyệt giao dịch nhỏ < 50.000 VNĐ" (User Opt-in Auto-approve).
2. Tỷ lệ người dùng từ chối đề xuất khoản vay hoặc tiết kiệm tại Gate 1 vượt quá 50%, cho thấy thuật toán gợi ý của `FinancialAdvisoryAgent` chưa phù hợp với thực tế và cần tinh chỉnh prompt/rules.

---

Nhận xét cuối cùng: "AI đề xuất, Người dùng quyết định" là cam kết đạo đức và kỹ thuật cao nhất của OnisAgent. 3 Chốt kiểm soát HITL bảo đảm rằng trợ lý AI luôn là người bạn đồng hành đáng tin cậy, tận tụy và an toàn cho người dùng cá nhân.
