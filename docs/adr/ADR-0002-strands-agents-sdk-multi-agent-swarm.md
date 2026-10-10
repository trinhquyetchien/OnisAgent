---
id: ADR-0002
timestamp: 2026-10-10T00:00:00Z
status: accepted
deciders: Trịnh Quyết Chiến, Hứa Huỳnh Anh
tags: [onisagent, aws, agentic-ai, strands-sdk, multi-agent, swarm, bedrock, task-management, personal-finance]
related_adrs: [ADR-0001]
---

# ADR-0002: Lựa chọn Strands Agents SDK và Kiến trúc Multi-Agent Swarm cho Tài chính & Công việc

> **Y-Statement:** Trong ngữ cảnh mở rộng phạm vi ứng dụng OnisAgent bao gồm cả quản lý dòng tiền tài chính lẫn quản lý công việc/kế hoạch cá nhân trên AWS, đối mặt với nguy cơ quá tải ngữ cảnh (token bloat) và tỷ lệ chọn nhầm công cụ (tool misfire) của mô hình Single Agent, chúng tôi quyết định sử dụng **Strands Agents SDK** và mô hình **Multi-Agent Swarm** để phân tách trách nhiệm giữa các Agent chuyên biệt (Phân loại Thu Chi, Cố vấn Tài chính, Quản lý Nhiệm vụ/Deadline), đạt được tính mô-đun hóa cao và tích hợp với AWS Bedrock AgentCore, chấp nhận tăng độ phức tạp khi điều phối luồng chuyển tiếp (handoff) giữa các Agent.

### 2.1. Problem Statement & Architectural Intent (Bài toán & Ý tưởng Kiến trúc)

**Bài toán (Context):**

- Đề cương mới của OnisAgent hợp nhất hai miền nghiệp vụ chính:

1. **Quản lý dòng tiền cá nhân:** Trích xuất hóa đơn, phân loại thu/chi và phân tích ngân sách theo quy tắc 50/30/20.
2. **Quản lý công việc và thời gian:** Theo dõi deadline, sắp xếp thứ tự ưu tiên nhiệm vụ và hỗ trợ lập kế hoạch cá nhân.

- Nếu tích hợp toàn bộ System Prompt và danh sách Tools của cả hai miền nghiệp vụ vào một Single Agent duy nhất:

- Kích thước Prompt tăng đáng kể (Prompt Token Bloat).
- Độ chính xác khi lựa chọn Tool giảm (Tool Misfire).
- Chi phí token tăng.
- Độ trễ phản hồi có nguy cơ vượt SLA 3 giây.

**Mục đích kiến trúc (Intent):**

Áp dụng nguyên tắc Phân tách Trách nhiệm (Separation of Concerns), chia hệ thống thành ba Agent chuyên biệt:

1. `CategorizationAgent`: Chuyên trích xuất văn bản từ hóa đơn, phân loại thu/chi và gán nhãn dữ liệu phù hợp.
2. `FinancialAdvisoryAgent`: Chuyên xử lý số liệu tài chính, phân tích xu hướng dòng tiền và tư vấn ngân sách theo quy tắc 50/30/20.
3. `TaskManagerAgent`: Chuyên quản lý danh sách công việc, nhắc nhở deadline và sắp xếp thứ tự ưu tiên.

Sử dụng **Strands Agents SDK**, Python SDK mã nguồn mở do AWS phát triển, để xây dựng và điều phối luồng Swarm/Orchestration, hướng đến triển khai trên **Amazon Bedrock AgentCore**.

### 2.2. Options Considered & Rejection Reasons (Các phương án & Lý do bác bỏ)

| Phương án | Ưu điểm (Pros) | Nhược điểm (Cons) | Lý do bác bỏ / lựa chọn |
|---|---|---|---|
| **Option A: Single Agent Architecture** | Đơn giản, dễ lập trình ban đầu, không phát sinh chi phí handoff giữa các Agent. | Prompt phình to khi kết hợp cả nghiệp vụ Tài chính và Quản lý Công việc; nguy cơ gọi nhầm Tool tăng khi số lượng chức năng mở rộng. | **BÁC BỎ:** Khó duy trì tính mô-đun và mở rộng tính năng; có nguy cơ khiến độ trễ vượt mục tiêu 3 giây. |
| **Option B: LangChain / CrewAI Framework** | Cộng đồng lớn, hệ sinh thái thư viện phong phú và nhiều tài liệu hướng dẫn. | Có thể phát sinh thêm lớp abstraction và phụ thuộc; cần đánh giá khả năng tích hợp, đóng gói và vận hành trên Amazon Bedrock AgentCore cũng như mức độ hỗ trợ MCP của phiên bản được lựa chọn. | **BÁC BỎ:** Không phải phương án ưu tiên cho kiến trúc hướng AWS của dự án nếu việc tích hợp và vận hành làm tăng độ phức tạp hoặc chi phí đáng kể. |
| **Option C: Strands Agents SDK + Multi-Agent Swarm** | SDK mã nguồn mở, tích hợp với hệ sinh thái AWS, hỗ trợ MCP; các Agent chuyên biệt giúp tách biệt Prompt, Tools và trách nhiệm nghiệp vụ. | Tăng độ phức tạp khi quản lý trạng thái chia sẻ (Shared Memory/State), chuyển tiếp ngữ cảnh và xử lý lỗi giữa các Agent. | **ĐƯỢC CHỌN:** Phù hợp với định hướng kiến trúc mô-đun, hỗ trợ điều phối Multi-Agent và thuận lợi cho lộ trình triển khai AWS của OnisAgent. |

**Phân tích sâu**

- Với `Single Agent`, hệ thống dễ phát triển ở giai đoạn đầu nhưng nhanh chóng gặp rào cản khi nghiệp vụ mở rộng: prompt lớn hơn, tool và định nghĩa hành vi chồng chéo, lại tăng khả năng chọn sai tool. Đối với hệ thống tài chính và quản lý nhiệm vụ, đây là vấn đề nghiêm trọng vì phản hồi sai hoặc rườm rà làm giảm niềm tin người dùng.
- Với `LangChain` hoặc `CrewAI`, nền tảng mạnh về cộng đồng nhưng cần đánh giá thêm về mức độ đóng gói, độ phù hợp với AWS-native runtime và chi phí vận hành. Không có bằng chứng cho thấy các framework này là không thể triển khai trên AWS, nhưng trong phạm vi của dự án, chúng không phải là lựa chọn ưu tiên nếu kéo theo thêm lớp abstraction mà không tạo ra lợi thế rõ ràng về hiệu năng hoặc độ tương thích hạ tầng.
- Với `Strands Agents SDK + Multi-Agent Swarm`, nguyên tắc tách nhiệm được giữ rõ nhất: mỗi Agent có prompt, tool và mục tiêu riêng. Chúng ta chấp nhận mất đi độ đơn giản ban đầu nhưng đổi lại được cải thiện độ mô-đun hóa, khả năng bảo trì, và khả năng kiểm soát chi phí token cũng như độ trễ.

### 2.3. Directives & Rules (Quy định bắt buộc)

**MUST:**

Mỗi Agent MUST được định nghĩa trong một mô-đun riêng biệt thuộc `src/agents/`:

- `src/agents/categorization_agent.py`
- `src/agents/financial_advisory_agent.py`
- `src/agents/task_manager_agent.py`

**MUST NOT:**

Codebase MUST NOT gộp chung System Prompt hoặc danh sách Tools của miền Tài chính vào miền Quản lý Công việc.

**ALWAYS:**

- ALWAYS sử dụng JSON chuẩn hóa để trao đổi ngữ cảnh giữa các Agent thông qua cơ chế handoff phù hợp với Strands SDK.
- Xác định rõ cấu trúc dữ liệu đầu vào và đầu ra của từng Agent.
- Quy định cách xử lý lỗi, dữ liệu thiếu, phản hồi sai định dạng và giới hạn số lần handoff.
- Chỉ truyền dữ liệu cần thiết giữa các Agent để hạn chế token bloat và tránh chia sẻ thông tin không liên quan.
- Phân biệt rõ dữ liệu nghiệp vụ, trạng thái hội thoại và bộ nhớ phiên (Session Memory).
- Không để Agent tư vấn tài chính tự ý thực hiện thao tác ghi dữ liệu hoặc thay đổi công việc nếu chưa có quyền hạn và cơ chế xác nhận phù hợp.

### 2.4. Consequences & Acceptance Criteria (Hệ quả & Tiêu chuẩn nghiệm thu)

**Tác động tích cực kỳ vọng:**

- Mục tiêu giảm hơn 40% kích thước Prompt trung bình so với kiến trúc Single Agent.
- Mục tiêu đạt độ chính xác chọn Tool trên 95%.
- Mã nguồn rõ ràng, cho phép Trịnh Quyết Chiến và Hứa Huỳnh Anh phát triển, kiểm thử các Agent tương đối độc lập.
- Tăng khả năng mở rộng nghiệp vụ tài chính và quản lý công việc mà không phải thay đổi toàn bộ kiến trúc.

**Đánh đổi / Nợ kỹ thuật:**

- Cần quản lý bộ nhớ phiên (Session Memory) và trạng thái chia sẻ chặt chẽ.
- Cần kiểm thử luồng handoff, lỗi giao tiếp và trường hợp Agent không trả về kết quả hợp lệ.
- Cần theo dõi chi phí token, độ trễ, tỷ lệ gọi Tool sai và tỷ lệ hoàn thành tác vụ.
- Cần xác định chính sách bảo mật, quyền truy cập dữ liệu và thời hạn lưu trữ bộ nhớ.
- Cần bảo đảm Agent xử lý thông tin tài chính và công việc đúng phạm vi quyền hạn.

**Tiêu chuẩn nghiệm thu:**

1. 100% các Agent được khởi tạo thành công bằng Strands Agents SDK.
2. Thời gian luân chuyển thông điệp giữa các Agent không quá 500 ms trong điều kiện kiểm thử đã xác định.
3. Vượt qua toàn bộ bộ kiểm thử tích hợp E2E trong thư mục `tests/`.
4. Có unit test cho từng Agent và các luồng handoff quan trọng.
5. Có kiểm thử cho lỗi timeout, dữ liệu JSON không hợp lệ, Agent không phản hồi và vượt giới hạn handoff.
6. Đánh giá hiệu năng trên bộ dữ liệu kiểm thử đại diện cho cả nghiệp vụ tài chính và quản lý công việc.
7. Xác minh mục tiêu giảm hơn 40% Prompt Token và độ chính xác chọn Tool trên 95% bằng benchmark có phương pháp đo, dữ liệu đầu vào và kết quả đối chứng rõ ràng.

**Lưu ý:** Các chỉ số 40%, 95%, 500 ms và SLA 3 giây là mục tiêu nghiệm thu, không phải kết quả đã được xác minh nếu chưa có số liệu đo thực tế.

### 2.5. Revisit Triggers (Điều kiện xem xét lại)

Xem xét lại quyết định kiến trúc khi xảy ra một trong các trường hợp:

- Thời gian phản hồi toàn luồng Swarm vượt 3,0 giây trên 15% tổng số truy vấn trong bộ đo được xác định trước.
- AWS phát hành SDK hoặc cơ chế điều phối mới có thể thay thế Strands Agents SDK và mang lại lợi ích rõ ràng về hiệu năng, chi phí hoặc khả năng vận hành.
- Chi phí token, độ trễ hoặc tỷ lệ lỗi vượt ngưỡng đã thống nhất.
- Số lượng Agent hoặc độ phức tạp điều phối tăng đến mức cần cân nhắc kiến trúc phân cấp hoặc cơ chế điều phối khác.
- Các yêu cầu về quyền riêng tư, bảo mật hoặc tính nhất quán dữ liệu thay đổi đáng kể.

---

Nhận xét cuối cùng: Quyết định này xác nhận rằng OnisAgent không nên xây dựng một Single Agent “tất cả trong một” khi phạm vi ứng dụng vừa gồm tài chính vừa gồm quản lý công việc; điều này dễ dẫn đến prompt phình to, tool misfire và latency tăng. Thay vào đó, chúng ta chọn kiến trúc Multi-Agent Swarm trên Strands Agents SDK để phân tách rõ ràng trách nhiệm giữa các Agent chuyên biệt, đồng thời giữ khả năng triển khai phù hợp với AWS Bedrock AgentCore. Đây là sự đánh đổi hợp lý giữa độ mô-đun, khả năng mở rộng và kiểm soát chi phí, trong khi vẫn bảo toàn triết lý kiến trúc của dự án: “Models reason, software computes.”
