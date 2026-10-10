---
id: ADR-0001
timestamp: 2026-10-10T00:00:00Z
status: accepted
deciders: Trịnh Quyết Chiến, Hứa Huỳnh Anh
tags:
  - onis
  - aws
  - agentic-ai
  - bedrock
  - strands-sdk
  - decimal-math
  - dynamodb
related_adrs: []
---

# ADR-0001: Tách suy luận LLM khỏi tính toán tài chính bằng Decimal

> **Y-Statement:** Trong ngữ cảnh Onis cần xử lý các giao dịch tài chính cá nhân với độ chính xác cao, thời gian phản hồi tốt và mức rủi ro sai số thấp, chúng tôi quyết định tách phần suy luận của LLM khỏi phần tính toán tiền tệ bằng mã nguồn Python sử dụng `Decimal` để đạt được độ đúng đắn, khả năng giải thích và tính đáng tin cậy của báo cáo tài chính, đồng thời chấp nhận đánh đổi là tăng độ phức tạp trong thiết kế và yêu cầu kiểm thử kỹ hơn.

### 1. Problem Statement & Architectural Intent (Bài toán & Ý tưởng)

**Bài toán (Context):** Onis vận hành trong môi trường tài chính cá nhân, nơi các giao dịch và báo cáo báo cáo số dư, tỷ lệ chi tiêu, lợi nhuận ròng và ngân sách theo quy tắc 50/30/20 đều yêu cầu tính toán chính xác. LLM có thể đưa ra các giá trị gần đúng, làm tròn sai hoặc suy diễn thiếu kiểm chứng, đặc biệt trong các tình huống như số tiền từ hàng chục nghìn giao dịch, tỷ lệ phần trăm, số âm, số 0, và các trường hợp giá trị không hợp lệ như `NaN`, `Infinity` hay chuỗi không phải tiền tệ. Khi số liệu tài chính sai, người dùng tin tưởng vào hệ thống sai, làm giảm độ tin cậy của cả agent và giải pháp tổng thể. Ngoài ra, Onis cần hoạt động trên AWS Bedrock và DynamoDB, nên thiết kế phải phối hợp giữa mô hình suy luận và phần logic tính toán tách biệt để giảm rủi ro sai lệch và duy trì hiệu năng tổng thể.

**Mục đích kiến trúc (Intent):** Quyết định này nhằm đặt nền tảng cho nguyên tắc "Models reason, software computes" của Onis. Chúng tôi tách rõ trách nhiệm: LLM chịu trách nhiệm phân loại, phân tích, lập kế hoạch và khuyến nghị; mã nguồn chịu trách nhiệm tính toán các giá trị tài chính theo đúng quy tắc. Cách triển khai này giúp tăng độ chính xác, bảo mật dữ liệu, khả năng kiểm thử và khả năng bảo trì, đồng thời đảm bảo các kết quả tài chính có thể được giải thích và đối chiếu rõ ràng bằng logic có thể kiểm chứng.

### 2. Options Considered & Rejection Reasons (Các phương án & Lý do bác bỏ)

| Phương án | Ưu điểm (Pros) | Nhược điểm (Cons) | Lý do bác bỏ / lựa chọn |
|---|---|---|---|
| **[Phương án được chọn] Pure Python + `Decimal` cho mọi tính toán tài chính** | Đúng chuẩn cho tiền tệ, tránh sai số float, dễ kiểm thử, dễ huấn luyện/giải thích, phù hợp với triết lý Onis | Cần viết validation rõ ràng, thêm một lớp ràng buộc dữ liệu và kiểm thử cho các edge case | **ĐƯỢC CHỌN:** Đây là phương án phù hợp nhất với mục tiêu “software computes” và yêu cầu tính đúng đắn trong môi trường tài chính cá nhân. |
| [Phương án bác bỏ 1] Sử dụng `float` hoặc `double` cho số tiền và tỷ lệ | Dễ viết, không cần chuyển đổi dữ liệu phức tạp, nhanh để prototype | Bị sai số thập phân, gây sai lệch khi làm tròn, không phù hợp với dữ liệu tài chính và không thể kiểm soát tốt các giá trị vô hạn/không hợp lệ | **BÁC BỎ:** `float` không thể đảm bảo độ chính xác cần thiết cho số dư, chi phí và tỷ lệ phần trăm; đây là nguyên nhân trực tiếp gây ra lỗi tài chính và giảm niềm tin vào Agent. |
| [Phương án bác bỏ 2] Để LLM tự tính toán và tự quyết định các giá trị tiền tệ trong phản hồi | Tiện lợi cho prototype, định dạng gọn, ít code boilerplate ban đầu | Không thể kiểm soát được tính nhất quán, thiếu kiểm thử, dễ tạo ra con số không thể giải thích, rủi ro về quyết định tài chính và sai lệch trong báo cáo | **BÁC BỎ:** Onis phải quản lý dữ liệu cá nhân và các quyết định có tác động tới ngân sách; để LLM tự quyết định con số tài chính không phù hợp với yêu cầu an toàn, minh bạch và tính tin cậy của hệ thống. |

### 3. Directives & Rules (Quy định bắt buộc)

- Codebase MUST use `Decimal` for all financial calculations, including balance, expense ratio, budget allocation, and summaries.
- Codebase MUST NOT use built-in `float` for money values, revenue, costs, or percentages that will be presented to users or used in decision-making.
- Business logic MUST be isolated from LLM inference. The model MAY recommend or explain, but MUST NOT directly execute financial calculations that need deterministic correctness.
- All transaction amounts MUST be validated before use. Invalid values such as negative numbers, `NaN`, `Infinity`, and non-numeric strings MUST be rejected explicitly.
- Financial tool functions MUST be pure and deterministic whenever practical so they can be tested and reviewed independently from Agent runtime execution.
- LLM-generated output MUST be treated as advisory unless it has been checked by deterministic business logic or human approval, especially for actions affecting user money or budget plans.
- Onis MUST maintain a single conversion path from raw input to validated `Decimal` values to prevent inconsistent rounding behavior across components.
- The architecture MUST keep the tool layer as the source of truth for arithmetic and the Agent layer as the source of truth for reasoning, planning, and user interaction.

### 4. Consequences & Acceptance Criteria (Hệ quả & Tiêu chuẩn nghiệm thu)

#### A. Lợi ích đạt được

- Cải thiện đáng kể độ chính xác của các phép tính tài chính so với `float`.
- Nâng cao độ tin cậy, khả năng giải thích và khả năng kiểm thử của Agent.
- Tăng khả năng tuân thủ triết lý “Models reason, software computes” trong toàn bộ hệ thống.
- Hạn chế rủi ro sai số trong báo cáo số dư và phân tích chi tiêu trên nền tảng AWS Bedrock và agentic workflow.

#### B. Tác động và nợ kỹ thuật

- Yêu cầu thêm các hàm validation và các test case cho edge cases về tiền tệ.
- Tăng độ phức tạp trong stack so với một prototype đơn giản sử dụng `float`.
- Một số phần của hệ thống cần chuyển đổi dữ liệu từ chuỗi, JSON hoặc DynamoDB sang `Decimal` đúng cách để tránh lỗi kiểu dữ liệu.
- Chi phí vận hành và bảo trì vẫn phải quản lý cẩn thận, nhưng so với rủi ro sai số tài chính thì đây là mức chi phí hợp lý và có thể kiểm soát.

#### C. Tiêu chuẩn nghiệm thu (Acceptance Criteria)

- Unit test cho business logic MUST PASS 100% trên các chức năng liên quan đến tính toán số dư, chỉ tiêu và tỷ lệ chi phí.
- Tất cả các giá trị tiền tệ MUST sử dụng `Decimal` trong các phương thức tính toán và đầu ra hệ thống.
- Các trường hợp biên như số âm, số 0, số lớn, làm tròn, `NaN`, `Infinity`, và dữ liệu không hợp lệ MUST được kiểm thử và reject đúng cách.
- Hệ thống MUST có một lớp validation thống nhất để chuẩn hóa input trước khi thực hiện phép toán.
- Mọi hành động có ảnh hưởng đến kế hoạch ngân sách hoặc tài chính cá nhân MUST yêu cầu cơ chế phê duyệt hoặc kiểm tra của con người trước khi được ghi nhận như quyết định cuối cùng.
- Kiểm thử phải xác nhận rằng Agent không thay thế logic tính toán bằng suy diễn ngẫu nhiên mà cần gọi tool xử lý tài chính có tính toán xác định.

### 5. Revisit Triggers (Điều kiện xem xét lại)

1. Nếu các phép tính tài chính phát hiện sai lệch lớn hơn 0% so với số liệu đã được xác minh hoặc đối chiếu thủ công, nhóm kiến trúc phải đánh giá lại việc sử dụng `Decimal` và các lớp validation hiện tại.
2. Nếu chức năng tính toán quá chậm hoặc vượt ngưỡng latency đề xuất (ví dụ: 95th percentile > 200 ms cho 1.000 giao dịch mẫu trong môi trường test), cần đánh giá lại thiết kế tool layer hoặc việc chuyển đổi dữ liệu.
3. Nếu một trong các service AWS hoặc SDK mới tạo ra dữ liệu tiền tệ dưới dạng kiểu không tương thích với `Decimal`, cần cập nhật kiến trúc và validation layer trước khi tiếp tục dùng trong production.
4. Nếu phát hiện bất kỳ luồng nào cho phép LLM trực tiếp định nghĩa số dư hoặc kế hoạch tiền tệ mà không đi qua business logic, cần xem xét lại mô hình chia tách trách nhiệm và thêm ràng buộc.
5. Nếu tổng chi phí vận hành AWS hoặc sử dụng Bedrock vượt quá ngân sách phê duyệt do cần thêm kiểm tra hoặc điều phối agent, nhóm phải đánh giá lại các quyết định thiết kế và tối ưu hóa hiệu năng.

---

Nhận xét cuối cùng: Quyết định này không đơn thuần là ưu tiên kỹ thuật cho một thư viện tính toán, mà là sự xác nhận rõ ràng về kiến trúc: Onis phải dựa trên logic chính xác và có kiểm soát để biến suy luận của LLM thành kết quả tài chính đáng tin cậy, minh bạch và an toàn cho người dùng.
