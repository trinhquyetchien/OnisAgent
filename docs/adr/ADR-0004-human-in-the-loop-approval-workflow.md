---
id: ADR-0004
timestamp: 2026-10-10T00:00:00Z
status: accepted
deciders: Trịnh Quyết Chiến, Hứa Huỳnh Anh
tags: [onisagent, hitl, human-in-the-loop, guardrails, security, compliance, user-approval]
related_adrs: [ADR-0001, ADR-0002, ADR-0003]
---

# ADR-0004: Thiết lập Cơ chế Kiểm soát Người dùng (Human-in-the-Loop Approval Workflow)

> **Y-Statement:** Trong ngữ cảnh OnisAgent thực hiện trích xuất/gán nhãn giao dịch tài chính, phân bổ lại kế hoạch ngân sách 50/30/20 và tự động sắp xếp deadline công việc, đối mặt với rủi ro sai sót tự nhiên của mô hình AI và yêu cầu tính minh bạch/an toàn tài chính cao, chúng tôi quyết định thiết lập **Cơ chế Kiểm soát Người dùng (Human-in-the-Loop - HITL)** cho tất cả các thao tác thay đổi dữ liệu quan trọng, chấp nhận việc tăng thêm một bước tương tác (friction) trên giao diện người dùng.

### 1. Problem Statement & Architectural Intent (Bài toán & Ý tưởng Kiến trúc)

**Bài toán (Context):**

Các Autonomous Agents có thể hiểu sai ý định, nhầm lẫn ngữ cảnh hoặc tạo ra đề xuất không phù hợp. Khi Agent có quyền trực tiếp ghi hoặc xóa dữ liệu tài chính cá nhân hay danh sách công việc quan trọng, lỗi suy luận có thể biến thành thay đổi dữ liệu dai dẳng mà người dùng không mong muốn.

Các tình huống rủi ro bao gồm:

- AI gán nhầm danh mục hoặc loại thu/chi cho một giao dịch.
- AI đề xuất hoặc áp dụng một kế hoạch thay đổi ngân sách 50/30/20 mà người dùng chưa xem xét.
- AI thay đổi thời hạn hoặc mức ưu tiên công việc dựa trên yêu cầu mơ hồ hay ngữ cảnh không đầy đủ.
- Người dùng không thể nhận biết thay đổi nào do AI đề xuất, thay đổi nào đã được lưu, hoặc cách khôi phục thay đổi sai.

Việc chỉ ghi log sau khi Agent đã tự thay đổi dữ liệu không loại bỏ rủi ro: người dùng phải chủ động tìm và sửa dữ liệu đã sai, đồng thời có thể không phát hiện được thay đổi không mong muốn.

**Mục đích kiến trúc (Intent):**

Áp dụng nguyên tắc **“AI đề xuất, Người dùng quyết định” (AI Proposes, Human Disposes)**. Các thay đổi quan trọng phải đi qua một Approval Gate trước khi được ghi nhận:

1. Với phân loại giao dịch, hiển thị dữ liệu liên quan, danh mục do AI đề xuất và cho phép người dùng chấp nhận hoặc chỉnh sửa.
2. Với kế hoạch ngân sách 50/30/20, yêu cầu người dùng xem xét và bấm “Xác nhận áp dụng” trước khi lưu.
3. Với thay đổi deadline hoặc mức ưu tiên công việc có ảnh hưởng đáng kể, hiển thị nội dung thay đổi để người dùng xác nhận trước khi ghi.
4. Ghi nhận quyết định chấp nhận, chỉnh sửa hoặc từ chối cùng thông tin kiểm toán cần thiết để giải thích thay đổi và hỗ trợ cải thiện đề xuất sau này.

HITL là một lớp kiểm soát quanh hành động có tác động; nó không thay thế validation nghiệp vụ, phân quyền truy cập hoặc tính toán xác định. Các phép tính tài chính vẫn phải tuân thủ ADR-0001, các Agent vẫn phải tuân thủ phân tách trách nhiệm trong ADR-0002, và dữ liệu lưu trữ vẫn theo các ranh giới của ADR-0003.

### 2. Options Considered & Rejection Reasons (Các phương án & Lý do bác bỏ)

| Phương án | Ưu điểm (Pros) | Nhược điểm (Cons) | Lý do bác bỏ / lựa chọn |
|---|---|---|---|
| **Option A: Full Autonomy (Tự động hoàn toàn)** | Trải nghiệm liền mạch; không cần bước xác nhận; tác vụ có thể hoàn tất nhanh hơn. | AI có thể áp dụng thay đổi sai mà người dùng không nhận biết; giảm khả năng kiểm soát và gây khó khăn cho việc truy nguyên hoặc khôi phục. | **BÁC BỎ:** Không phù hợp với mức độ nhạy cảm của dữ liệu tài chính và các thay đổi công việc quan trọng. Độ chính xác mô hình không thể được xem là bảo đảm tuyệt đối. |
| **Option B: Passive Logging Only (Chỉ ghi log)** | Tác vụ vẫn tự động; có lịch sử để kiểm tra sau; ít gây gián đoạn lúc sử dụng. | Việc ghi log không ngăn thay đổi sai; người dùng phải dò tìm và sửa dữ liệu sau khi sự việc xảy ra; người dùng có thể không nhận thấy thay đổi. | **BÁC BỎ:** Chỉ hỗ trợ điều tra hậu kiểm, không ngăn dữ liệu sai được ghi nhận và không duy trì quyền quyết định của người dùng trước khi thay đổi có hiệu lực. |
| **Option C: Interactive HITL Approval Gate** | Người dùng xem được đề xuất trước khi áp dụng; có thể chấp nhận, chỉnh sửa hoặc từ chối; tạo cơ sở ghi nhận phản hồi có kiểm soát. | Thêm tương tác vào luồng; cần quản lý trạng thái chờ duyệt, hết hạn, gửi lại và lỗi khi ghi; có thể làm tác vụ hoàn tất chậm hơn. | **ĐƯỢC CHỌN:** Cân bằng giữa khả năng hỗ trợ tự động của AI và quyền kiểm soát của người dùng đối với các thay đổi quan trọng. |

**Đánh đổi:** Full autonomy có thể giảm số thao tác nhưng chuyển rủi ro sai sót sang dữ liệu đã lưu. Passive logging cải thiện khả năng truy vết nhưng không chặn được sai sót. Approval Gate làm tăng friction và chi phí triển khai giao diện/backend, đổi lại bảo đảm rằng đề xuất quan trọng chưa trở thành thay đổi dai dẳng cho đến khi có hành động xác nhận rõ ràng của người dùng. Cơ chế này giảm rủi ro nhưng không thể bảo đảm “100% chính xác” hoặc loại bỏ mọi nguy cơ do lỗi hệ thống, tài khoản bị xâm phạm hay thao tác nhầm của người dùng.

### 3. Directives & Rules (Quy định bắt buộc)

- **MUST NOT:** Codebase MUST NOT tự động cập nhật hoặc xóa dữ liệu giao dịch, kế hoạch ngân sách hoặc công việc quan trọng nếu chưa nhận được xác nhận rõ ràng từ người dùng cho đúng đề xuất đang chờ duyệt.
- **MUST:** Approval Gate MUST gắn xác nhận với nội dung, phiên bản và người dùng cụ thể của đề xuất; không được áp dụng một xác nhận cũ cho đề xuất đã thay đổi.
- **MUST:** Giao diện Recommendation MUST cung cấp lựa chọn “Chấp nhận” và “Chỉnh sửa”; với đề xuất có thể bị từ chối mà không gây dữ liệu không hợp lệ, giao diện SHOULD cung cấp thêm lựa chọn “Từ chối”.
- **MUST:** Hệ thống MUST phân biệt trạng thái `pending`, `approved`, `edited`, `rejected`, `expired` và `failed` (hoặc các trạng thái tương đương có cùng ý nghĩa), đồng thời chỉ thực hiện thao tác ghi sau bước xác nhận tương ứng.
- **MUST:** Backend MUST kiểm tra quyền truy cập, tính hợp lệ nghiệp vụ và trạng thái hiện tại trước khi ghi dữ liệu; ẩn hoặc vô hiệu hóa nút trên giao diện không được xem là kiểm soát truy cập đủ.
- **MUST:** Thao tác ghi sau xác nhận MUST tránh áp dụng lặp do retry hoặc double-click, ví dụ bằng mã đề xuất/idempotency key và kiểm tra phiên bản dữ liệu phù hợp.
- **MUST:** Hành động chỉnh sửa chỉ được ghi sau khi người dùng gửi/chấp thuận nội dung đã sửa. Việc chỉ mở hoặc thay đổi tạm thời giá trị trên biểu mẫu MUST NOT tự ghi dữ liệu.
- **ALWAYS:** ALWAYS ghi lại trạng thái đề xuất, quyết định của người dùng, thời điểm và tham chiếu bản ghi liên quan vào nơi lưu trữ phù hợp. Nội dung log MUST được giới hạn ở mức cần thiết cho kiểm toán, không ghi bí mật hoặc dữ liệu nhạy cảm không cần thiết.
- **MUST:** Phản hồi sửa danh mục có thể được lưu trong lịch sử phiên `ChatSessions` để hỗ trợ cải thiện đề xuất sau này, nhưng MUST được phân vùng theo `user_id`, giới hạn mục đích sử dụng, có chính sách lưu giữ/xóa và không được đưa vào Few-shot Prompting cho người dùng khác.
- **MUST NOT:** Dữ liệu phản hồi hoặc Correction History MUST NOT được coi là sự thật đã xác minh nếu chưa qua xác nhận; dữ liệu nhạy cảm MUST NOT được đưa vào prompt hoặc log nếu không cần thiết cho tác vụ.
- **MUST:** Agent tư vấn tài chính MUST NOT tự ý thực hiện thao tác ghi dữ liệu hoặc thay đổi công việc chỉ dựa trên nội dung đề xuất của mình. Quyền thực thi phải được kiểm tra ở tầng ứng dụng/dịch vụ sau xác nhận.
- **MUST:** Các giá trị tiền tệ trong đề xuất và nội dung đã xác nhận MUST tiếp tục được tính toán/kiểm tra bằng logic xác định theo ADR-0001; xác nhận người dùng không thay thế validation số học.

### 4. Consequences & Acceptance Criteria (Hệ quả & Tiêu chuẩn nghiệm thu)

#### A. Tác động tích cực kỳ vọng

- Giảm nguy cơ AI tự ý ghi nhận phân loại sai hoặc áp dụng kế hoạch ngân sách không được người dùng đồng ý.
- Tăng tính minh bạch: người dùng có thể xem đề xuất, sửa hoặc từ chối trước khi thay đổi có hiệu lực.
- Tạo lịch sử quyết định để hỗ trợ điều tra lỗi, kiểm thử chất lượng Agent và cải thiện đề xuất theo phạm vi người dùng.
- Giữ cho quyền thực thi thay đổi quan trọng ở tầng ứng dụng có kiểm tra, thay vì trao quyền ghi dữ liệu trực tiếp cho Agent.

#### B. Tác động tiêu cực / Nợ kỹ thuật

- Phải quản lý `Pending Approval State` trong phiên Streamlit hoặc dịch vụ trạng thái tương ứng; `st.session_state` chỉ nên được xem là trạng thái giao diện, không phải nguồn xác thực duy nhất cho phép ghi.
- Cần xử lý đề xuất hết hạn, dữ liệu đã thay đổi kể từ lúc đề xuất, lỗi lưu, retry và trường hợp người dùng gửi nhiều lần.
- Thêm bước xem xét có thể làm giảm tốc độ hoàn tất tác vụ hoặc khiến người dùng bỏ dở; cần đo lường thay vì giả định mức ảnh hưởng.
- Lưu correction history làm phát sinh trách nhiệm về phân quyền, quyền riêng tư, thời hạn lưu giữ và xóa dữ liệu.
- HITL không loại bỏ lỗi do người dùng xác nhận nhầm, lỗi ứng dụng, hành vi trái phép hoặc sai lệch trong nội dung đề xuất.

#### C. Tiêu chuẩn nghiệm thu (Acceptance Criteria)

1. UI phải hiển thị đề xuất phân loại giao dịch, đề xuất ngân sách 50/30/20 và các thay đổi công việc thuộc phạm vi HITL trước khi các thay đổi đó được ghi.
2. Kiểm thử backend phải xác nhận rằng không thể ghi hoặc xóa thay đổi quan trọng khi đề xuất đang `pending`, bị từ chối, hết hạn hoặc không thuộc người dùng đang xác thực.
3. Hành động “Chấp nhận” và gửi nội dung đã “Chỉnh sửa” phải ghi đúng giá trị đã xem xét; thao tác chỉnh sửa cục bộ chưa gửi MUST NOT làm thay đổi dữ liệu lưu trữ.
4. Có unit/integration tests cho ít nhất các trường hợp: chấp nhận hợp lệ, chỉnh sửa và xác nhận, từ chối, timeout/hết hạn, payload không hợp lệ, dữ liệu nền đã đổi, lỗi ghi, retry và gửi lặp.
5. Kiểm thử phải xác nhận rằng thao tác lặp không tạo ra các thay đổi trùng lặp hoặc áp dụng một đề xuất cũ lên dữ liệu mới.
6. Correction History phải gắn đúng `user_id`; kiểm thử phân quyền MUST xác nhận rằng người dùng không thể đọc hoặc sử dụng phản hồi của người dùng khác.
7. Không dùng “loại bỏ 100% nguy cơ” làm tiêu chí nghiệm thu. Mức giảm lỗi, tỷ lệ người dùng chấp nhận/chỉnh sửa và tác động lên thời gian hoàn tất phải được đo trên tập dữ liệu hoặc quy trình thử nghiệm có phương pháp được ghi lại.

### 5. Revisit Triggers (Điều kiện xem xét lại)

- Khi `CategorizationAgent` đạt confidence score trên 98% liên tục trong ít nhất 500 giao dịch của cùng một người dùng trên tập đánh giá được xác định trước, nhóm có thể **đề xuất đánh giá** chế độ auto-approve tự chọn cho phạm vi rủi ro thấp. Đây không phải quyền tự động tắt HITL; thay đổi cần được đánh giá rủi ro, có opt-in rõ ràng, khả năng hoàn tác và phê duyệt kiến trúc riêng.
- Khi tỷ lệ người dùng bỏ dở hoặc thời gian hoàn tất tác vụ tăng đáng kể do Approval Gate theo dữ liệu đo được, nhóm cần xem xét cách giảm friction mà không bỏ kiểm soát với thay đổi rủi ro cao.
- Khi xảy ra bất kỳ thay đổi tài chính quan trọng nào không có xác nhận hợp lệ hoặc bị ghi nhầm người dùng, cần dừng/giới hạn luồng liên quan, điều tra nguyên nhân và đánh giá lại cơ chế xác thực, idempotency và cách ly tenant.
- Khi chính sách quyền riêng tư, yêu cầu tuân thủ hoặc thời hạn lưu giữ Correction History thay đổi, cần đánh giá lại cách lưu phản hồi và sử dụng chúng trong các phiên sau.
- Khi loại tác vụ mới được bổ sung có tác động đáng kể đến tài chính, dữ liệu cá nhân hoặc cam kết thời gian của người dùng, cần xác định rõ mức rủi ro và yêu cầu HITL trước khi cấp quyền ghi cho Agent.

---

Quyết định này đặt người dùng làm chủ thể phê duyệt các thay đổi quan trọng: Agent có thể đề xuất và giải thích, nhưng ứng dụng chỉ ghi thay đổi sau khi xác thực quyền, kiểm tra hợp lệ và nhận được xác nhận phù hợp. Cơ chế HITL giảm rủi ro tự động hóa không mong muốn nhưng không thay thế các biện pháp bảo mật, validation hoặc giám sát vận hành khác.
