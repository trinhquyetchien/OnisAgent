---
id: ADR-0001
timestamp: 2026-10-10T00:00:00Z
status: accepted
deciders: Trịnh Quyết Chiến, Hứa Huỳnh Anh
tags:
  - onisagent
  - aws
  - agentic-ai
  - bedrock
  - ollama
  - strands-sdk
  - decimal-math
  - fast-path
  - system-1
  - system-2
  - kev-model
  - aws-lambda
related_adrs: [ADR-0002, ADR-0003, ADR-0004, ADR-0005]
---

# ADR-0001: Kiểm thử Decimal cho Máy tính khoản vay dư nợ giảm dần & Số dư sổ cái

> **Y-Statement:** Trong ngữ cảnh Onis cần kiểm chứng chính xác số dư sổ cái và toàn bộ lịch trả góp gốc + lãi của khoản vay dư nợ giảm dần, chúng tôi quyết định lấy hai đối tượng này làm trọng tâm kiểm thử hồi quy cho số học tiền tệ bằng Python `Decimal`. Các phép tính được thực thi bằng phần mềm (AWS Lambda trong môi trường triển khai), không giao cho LLM tự tính. Lệnh đơn giản như ghi nhận thu chi, tạo task hoặc xem số dư có thể đi qua **Fast Path (System 1 / Kev Model)** với mục tiêu **~5–12 ms, 0 Token LLM**; yêu cầu dự toán khoản vay đi qua **Reasoning Path (System 2 / Amazon Bedrock / Ollama)** để phân tích, nhưng mọi con số trong kết quả vẫn phải do calculator `Decimal` cung cấp trước khi LLM diễn giải.

---

### 1. Problem Statement & Architectural Intent (Bài toán & Ý tưởng)

**Bài toán (Context):** 
Onis cần tính toán số dư sổ cái, phân bổ thu chi và lập lịch trả góp khoản vay dư nợ giảm dần với độ chính xác tuyệt đối 100%. Các giao dịch và chỉ số tài chính (như số dư khả dụng, tổng thu chi, hạn mức chi tiêu, dự toán khoản vay trả góp dư nợ giảm dần, và số dư quỹ tiết kiệm) đòi hỏi tính toán toán học chuẩn xác tuyệt đối ($100\%$). Các mô hình ngôn ngữ lớn (LLM) dù tiên tiến đến đâu cũng vốn là các mô hình xác suất sinh từ tiếp theo (probabilistic token predictors), không phải bộ vi xử lý số học tất định (deterministic arithmetic engines). Khi giao việc tính toán số học cho LLM, hệ thống đối mặt với 3 nghịch lý nghiêm trọng:
1. **Ảo giác số học (LLM Hallucination):** LLM dễ cộng trừ sai số tiền lớn, tính sai lãi suất lũy kế, làm tròn sai chữ số thập phân hoặc tự bịa ra số dư tài khoản không có thật.
2. **Lãng phí tài nguyên (LLM Overkill):** Tiêu tốn hàng trăm token đắt đỏ và tạo độ trễ cao (1.500 ms – 4.000 ms) chỉ để thực hiện các phép cộng trừ đơn giản mà máy tính có thể xử lý trong vài phần nghìn giây.
3. **Mất an toàn và độ tin cậy:** Người dùng mất niềm tin ngay lập tức nếu trợ lý AI hiển thị sai số dư tiền mặt hoặc báo cáo sai lệch tình hình dòng tiền và lịch nợ.

Ngoài ra, việc biểu diễn số tiền bằng kiểu dữ liệu dấu phẩy động thông thường (`float` / `double`) trong các ngôn ngữ lập trình tiềm ẩn lỗi làm tròn nhị phân chuẩn IEEE 754 (ví dụ: `0.1 + 0.2 = 0.30000000000000004`), gây sai lệch số dư theo thời gian.

**Mục đích kiến trúc (Intent):** 
Quyết định này thiết lập nguyên tắc nền tảng tối thượng của OnisAgent: **"Models reason, software computes"** (Mô hình suy luận, phần mềm tính toán). Chúng tôi phân định rõ ranh giới kiến trúc:
- **Fast Path (System 1 / Kev Decision Model):** Tiếp nhận tác vụ lặp lại có độ tin cậy cao như ghi thu chi, tạo task và xem số dư; các phép tính cần thiết dùng Python `Decimal` với mục tiêu độ trễ **~5–12 ms**, **0 Token LLM**.
- **Reasoning Path (System 2 / Bedrock / Ollama LLM):** Đảm nhiệm suy luận chiến lược như phân tích dòng tiền và dự toán khoản vay. Khi cần số liệu tài chính, kết quả phải được tính bằng tool Python `Decimal` (AWS Lambda trong triển khai) trước khi LLM diễn giải; LLM không tự thực hiện phép tính.

---

### 2. Options Considered & Rejection Reasons (Các phương án & Lý do bác bỏ)

| Phương án | Ưu điểm (Pros) | Nhược điểm (Cons) | Lý do bác bỏ / lựa chọn |
|---|---|---|---|
| **[Phương án được chọn] Python `Decimal` trên AWS Lambda, được gọi từ Fast Path hoặc Reasoning Path** | Tính tiền xác định, không sai số float; dễ viết unit test độc lập; giải thích minh bạch công thức tính. | Cần cài đặt tầng kiểm tra hợp lệ (validation) đầu vào nghiêm ngặt và chuyển đổi kiểu dữ liệu tương thích với DynamoDB / JSON. | **ĐƯỢC CHỌN:** Thực thi triết lý "Models reason, software computes"; đường đi của phép tính không phụ thuộc đường đi suy luận của yêu cầu. |
| [Phương án bác bỏ 1] Sử dụng kiểu số thực `float` / `double` thông thường | Viết code nhanh, tận dụng toán tử gốc của Python, không cần import thư viện `decimal`. | Dính lỗi sai số nhị phân IEEE 754, sai lệch khi làm tròn cộng dồn hàng nghìn giao dịch, không kiểm soát được giá trị vô cực (`Infinity`) hoặc `NaN`. | **BÁC BỎ:** Không đáp ứng tiêu chuẩn nghiêm ngặt của hệ thống quản lý dòng tiền cá nhân; gây thất thoát số dư và làm mất uy tín sản phẩm. |
| [Phương án bác bỏ 2] Để LLM tự tính toán số học trực tiếp trong Prompt / Narration | Giảm code boilerplate phía backend; cấu trúc code trông có vẻ gọn gàng ban đầu. | Nguy cơ ảo giác cực cao; tính toán sai lệch; lãng phí token (LLM Overkill); độ trễ cao (1.500–4.000 ms); không thể kiểm thử bằng unit test tất định. | **BÁC BỎ:** Vi phạm triệt để nguyên tắc an toàn tài chính; không cho phép LLM tự đóng vai trò máy tính số học. |

---

### 3. Directives & Rules (Quy định bắt buộc)

- **MUST (Bắt buộc dùng Decimal):** Codebase MUST sử dụng `Decimal` (từ module chuẩn `decimal` của Python) cho mọi phép toán liên quan đến tiền tệ, bao gồm: tính số dư sổ cái, phân bổ thu chi, máy tính khoản vay trả góp dư nợ giảm dần (`calculate_loan_amortization`), và tiến độ nạp quỹ tiết kiệm (`savings_goals`).
- **MUST NOT (Cấm dùng float):** Codebase MUST NOT sử dụng kiểu dữ liệu `float` hoặc `double` cho các trường lưu trữ tiền tệ, doanh thu, chi phí hoặc tỷ lệ phần trăm được trình bày tới người dùng hoặc dùng làm căn cứ ra quyết định.
- **MUST (Deterministic Calculation):** Số dư sổ cái và lịch trả góp gốc + lãi MUST được tính bằng Python `Decimal` (`src/tools/calculator.py`); khi triển khai AWS, Lambda handler dùng cùng phép tính. Dự toán khoản vay có thể được yêu cầu trên Reasoning Path, nhưng LLM chỉ diễn giải kết quả tool. Mục tiêu **~5–12 ms, 0 Token LLM** áp dụng cho tác vụ đủ điều kiện chạy Fast Path, không phải cho toàn bộ yêu cầu dự toán.
- **MUST (Ngăn chặn LLM tự sinh số học trên Reasoning Path):** Khi một truy vấn phức tạp được định tuyến qua **Reasoning Path (System 2 / Amazon Bedrock hoặc Ollama)** (ví dụ: `finance.analyze_spending`, `work.plan_day`), toàn bộ số liệu tài chính trong câu trả lời MUST được tính toán trước bởi các hàm Python `Decimal` thông qua cơ chế Grounded Context Injection hoặc Tool Call trước khi LLM sinh văn bản phản hồi. LLM chỉ được phép tạo lời thoại diễn giải (narration) dựa trên các con số đã được phần mềm tính sẵn; LLM **MUST NOT** tự ý cộng trừ nhân chia hoặc thay đổi số liệu trong văn bản đầu ra.
- **MUST (Input Validation):** Tất cả số tiền giao dịch đầu vào MUST được kiểm tra hợp lệ trước khi tính toán (`amount > 0`, không vượt trần giao dịch 1.000.000.000 VNĐ, từ chối chuỗi không phải số, chặn các giá trị `NaN` hoặc `Infinity`).
- **MUST (Deterministic & Pure Functions):** Các hàm nghiệp vụ trong `src/tools/calculator.py` MUST là các hàm thuần túy (pure functions), không phụ thuộc vào trạng thái ngẫu nhiên để có thể kiểm thử hồi quy 100% bằng Unit Test.
- **ALWAYS:** Duy trì một quy trình chuyển đổi dữ liệu duy nhất từ chuỗi đầu vào sang `Decimal` với chế độ làm tròn chuẩn hóa (`ROUND_HALF_UP` hoặc tương đương) để ngăn chặn hành vi làm tròn không nhất quán giữa các dịch vụ.

---

### 4. Consequences & Acceptance Criteria (Hệ quả & Tiêu chuẩn nghiệm thu)

#### A. Lợi ích đạt được
- **Độ chính xác số học đạt tuyệt đối 100%:** Minh chứng đanh thép cho triết lý *"Models reason, software computes"*, loại bỏ hoàn toàn lỗi làm tròn float và triệt tiêu nguy cơ ảo giác số học từ LLM.
- **Tối ưu hóa hiệu năng và chi phí:** Khoảng 85% tác vụ lặp lại được xử lý trên Fast Path trong **~5–12 ms** mà không phát sinh Token LLM; các yêu cầu suy luận vẫn dùng cùng calculator xác định khi cần số liệu.
- **Khả năng kiểm thử:** Các hàm tính số dư và lịch trả góp được kiểm thử độc lập bằng dữ liệu tham chiếu, gồm cả tính nhất quán từng kỳ và đầu ra của Lambda adapter.
- **Trải nghiệm người dùng mượt mà:** Phản hồi số liệu tài chính gần như tức thì, tạo điều kiện lý tưởng cho giao tiếp giọng nói hai chiều (Voice-First).

#### B. Đánh đổi và Nợ kỹ thuật
- Cần viết tầng chuyển đổi (serializer/deserializer) giữa `Decimal` của Python và kiểu dữ liệu của DynamoDB / JSON.
- Đòi hỏi xây dựng bộ kiểm tra ràng buộc dữ liệu (data validation) chặt chẽ cho tất cả các điểm tiếp nhận dữ liệu từ người dùng.

#### C. Tiêu chuẩn nghiệm thu (Acceptance Criteria)
1. **Unit Test Pass 100%:** `tests/test_tools.py` MUST kiểm chứng bằng kết quả tham chiếu số dư sổ cái và các kỳ trong lịch trả góp gốc + lãi; toàn bộ bài kiểm thử liên quan MUST PASS.
2. **Độ chính xác tính toán đạt 100%:** Đối chiếu kết quả của `src/tools/calculator.py` và AWS Lambda handlers với các thuật toán tham chiếu chuẩn ngân hàng cho kết quả trùng khớp $100\%$, sai lệch bằng $0$.
3. **Hiệu năng Fast Path:** Các tác vụ đủ điều kiện định tuyến qua Fast Path MUST đạt độ trễ trung bình $\le 12$ ms và tiêu tốn đúng **0 Token LLM** trên môi trường thử nghiệm chuẩn.
4. **Không xuất hiện số học tự sinh từ LLM:** Dù yêu cầu đi qua Reasoning Path (LLM), kết quả số học bắt buộc phải gọi qua tool Python `Decimal` trước khi LLM sinh văn bản phản hồi; kiểm thử tích hợp xác nhận $100\%$ các số liệu tài chính xuất hiện trong câu trả lời narration của LLM đều bắt nguồn từ ngữ cảnh do hàm Python `Decimal` cung cấp sẵn.

---

### 5. Revisit Triggers (Điều kiện xem xét lại)

Quyết định kiến trúc này cần được đánh giá lại nếu xảy ra một trong các trường hợp sau:
1. Phát hiện bất kỳ sai lệch nào (> $0\%$) giữa số dư do hệ thống tính toán và số liệu đối soát giao dịch thực tế.
2. Xuất hiện luồng xử lý mới cho phép LLM tự ý xuất ra các con số tài chính mà không thông qua hàm tính toán Python `Decimal`.
3. Thời gian xử lý của các hàm tính toán `Decimal` trên Fast Path (AWS Lambda) vượt quá 50 ms cho tập dữ liệu thông thường.
4. Nền tảng lưu trữ mới yêu cầu kiểu biểu diễn số học đặc thù mà `Decimal` không thể đáp ứng hiệu quả.

---

Nhận xét cuối cùng: "Models reason, software computes" là kim chỉ nam bất biến của OnisAgent. Việc kết hợp giữa độ chính xác của Python `Decimal` trên AWS Lambda và tốc độ siêu tốc của Fast Path (System 1) bảo đảm rằng OnisAgent luôn là một trợ lý tài chính chuẩn xác, đáng tin cậy và tối ưu chi phí.
