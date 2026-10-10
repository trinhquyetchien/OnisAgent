---
id: ADR-0003
timestamp: 2026-10-10T00:00:00Z
status: accepted
deciders: Trịnh Quyết Chiến, Hứa Huỳnh Anh
tags: [onisagent, aws, database, dynamodb, s3, hybrid-storage, serverless, no-sql]
related_adrs: [ADR-0001-decimal-money-calculation, ADR-0002-strands-agents-sdk-multi-agent-swarm]
---

# ADR-0003: Lựa chọn Cấu trúc Lưu trữ Dữ liệu Lai Amazon DynamoDB và Amazon S3

> **Y-Statement:** Trong ngữ cảnh ứng dụng OnisAgent cần quản lý song song dữ liệu có cấu trúc (giao dịch thu chi, danh sách công việc/deadline, lịch sử phiên chat) và dữ liệu phi cấu trúc (ảnh chụp hóa đơn, file sao kê CSV/PDF), đối mặt với yêu cầu độ trễ cực thấp (single-digit millisecond latency), tính năng Serverless Pay-as-you-go và khả năng mở rộng không giới hạn, chúng tôi quyết định sử dụng **Amazon DynamoDB** làm CSDL NoSQL chính kết hợp **Amazon S3** làm Blob Storage, chấp nhận việc không hỗ trợ các phép Join quan hệ phức tạp như RDBMS truyền thống.

### 1. Problem Statement & Architectural Intent (Bài toán & Ý tưởng Kiến trúc)

**Bài toán (Context):**

OnisAgent xử lý hai dạng dữ liệu khác biệt, mỗi dạng có yêu cầu lưu trữ và truy xuất khác nhau:

1. **Dữ liệu thao tác tần suất cao, kích thước nhỏ, truy vấn theo user**
   - Lịch sử thu chi, danh mục giao dịch, tasks, deadline, lịch sử phiên chat và Agent memory.
   - Đây là dữ liệu thường được đọc/ghi với tần suất cao, cần latency thấp và cấu trúc dễ truy vấn theo `user_id`, `transaction_id`, `task_id` hoặc `session_id`.

2. **Dữ liệu kích thước lớn, phi cấu trúc**
   - Ảnh chụp hóa đơn, PDF sao kê ngân hàng, file CSV/Excel do người dùng tải lên để trích xuất dữ liệu.
   - Đây là dữ liệu cần khả năng lưu file lớn, không giới hạn về dung lượng, và không nên nằm trong item DynamoDB vì giới hạn item size và chi phí phát sinh lớn khi lưu object lớn.

Một mô hình lưu trữ quan hệ truyền thống như Amazon RDS/PostgreSQL đem lại lợi ích về ACID và join mạnh, nhưng không phù hợp với mô hình serverless và AI Agent workflows của OnisAgent vì:

- Chi phí vận hành cố định và luôn bật máy chủ (always-on) không tối ưu cho mô hình pay-as-you-go.
- Khó tích hợp trực tiếp với AWS-native Agent memory, serverless runtime và model orchestration như Bedrock AgentCore.
- Không phải là cách tự nhiên nhất để lưu trữ dữ liệu dạng key-value/document của session, transaction và task state.

**Mục đích kiến trúc (Intent):**

Chúng tôi tách rõ hai tầng lưu trữ cho OnisAgent:

- **Amazon DynamoDB**: lưu trữ dữ liệu có cấu trúc và truy xuất nhanh theo user, với mô hình NoSQL phù hợp cho tài chính cá nhân, danh sách công việc, session metadata và agent memory.
- **Amazon S3**: lưu trữ file phương tiện và snapshot dữ liệu lớn như hóa đơn, PDF sao kê, CSV/Excel, nhằm giảm chi phí và tránh giới hạn item size của DynamoDB.

Mục tiêu là đạt được:

- độ trễ truy vấn thấp cho tuyến dữ liệu thao tác hàng ngày;
- mô hình serverless tối ưu về chi phí và khả năng mở rộng;
- khả năng cô lập dữ liệu theo người dùng (tenant isolation) bằng `user_id` và các key phân vùng rõ ràng;
- sự tách biệt giữa dữ liệu “metadata” và dữ liệu “blob” để quản lý tốt hơn ở tầng ứng dụng và Agent.

### 2. Options Considered & Rejection Reasons (Các phương án & Lý do bác bỏ)

| Phương án | Ưu điểm (Pros) | Nhược điểm (Cons) | Lý do bác bỏ / lựa chọn |
|---|---|---|---|
| **Option A: Relational Database Only (Amazon RDS / PostgreSQL)** | Hỗ trợ ACID, join và truy vấn thống kê phức tạp, phù hợp cho mô hình dữ liệu quan hệ truyền thống. | Chi phí vận hành cố định, thiếu tính serverless hiệu quả, khó tối ưu cho AI memory và key-value workflow, cần quản lý instance luôn chạy. | **BÁC BỎ:** Không phù hợp với nguyên tắc serverless pay-as-you-go và không tối ưu cho dạng dữ liệu agentic workflow làm việc chủ yếu theo `user_id` và document-style access patterns. |
| **Option B: DynamoDB Only (Lưu Base64 Image trong Item)** | Một nguồn dữ liệu duy nhất, dễ triển khai ban đầu. | Vượt giới hạn 400 KB/item của DynamoDB, tăng chi phí RCU/WCU rất nhanh, làm giảm hiệu năng đọc/ghi khi lưu dữ liệu lớn và ảnh đa phương tiện. | **BÁC BỎ:** Đây là anti-pattern đối với NoSQL khi lưu blob hoặc object lớn; không phù hợp với mô hình file và ảnh hoá đơn của OnisAgent. |
| **Option C: Hybrid Storage (DynamoDB + Amazon S3)** | Tối ưu chi phí serverless, truy xuất dữ liệu có cấu trúc nhanh, lưu trữ blob không giới hạn, tích hợp native với AWS SDK và phù hợp với Agent workflows trên AWS. | Cần quản lý bản ghi tham chiếu giữa `DynamoDB item` và `S3 object key`, đồng thời phải xây dựng policy kiểm tra và cleanup đối với dữ liệu khuyết hoặc hỏng. | **ĐƯỢC CHỌN:** Đây là phương án phù hợp nhất với yêu cầu về serverless, khả năng mở rộng, độ trễ thấp và lưu trữ file lớn. |

**Phân tích sâu**

- Với **Relational Database Only**, OnisAgent có thể dễ dàng lập trình trong giai đoạn đầu nhưng sớm đối mặt với chi phí vận hành và ràng buộc của một instance luôn bật. Hơn nữa, các dữ liệu như memory session, task state và metadata trên cơ sở `user_id` không cần các join phức tạp như một data warehouse. Đối với dự án AI agent, serverless-first và event-driven là ưu tiên cao hơn so với mô hình RDBMS cổ điển.
- Với **DynamoDB Only**, giải pháp đơn giản về mặt kiến trúc nhưng lại không thể đúng với yêu cầu lưu ảnh hóa đơn và các tệp lớn. Việc nhúng file bytes vào item sẽ phá vỡ cấu trúc item, làm tăng chi phí đọc/ghi, và không phù hợp khi dữ liệu lớn hơn nhiều so với giới hạn vào khoảng 400 KB. Đây là kiểu anti-pattern rõ ràng đối với một hệ thống có nhiều file phương tiện.
- Với **Hybrid Storage**, kiến trúc giữ được độ đơn giản cần thiết: DynamoDB lưu metadata và dữ liệu truy vấn nhanh, S3 lưu blob vật lý. Chúng ta chấp nhận cần thêm một mối liên kết giữa item và object key, nhưng đổi lại được chi phí hợp lý, khả năng mở rộng và hiệu suất rõ ràng hơn cho cả agent và người dùng.

### 3. Directives & Rules (Quy định bắt buộc)

- **MUST NOT:** Codebase MUST NOT lưu trực tiếp dữ liệu nhị phân (binary blobs / Base64 images) vào DynamoDB.
- **MUST:** Mỗi record giao dịch có đính kèm hóa đơn MUST lưu đường dẫn `s3_bucket_key` chỉ tới file tương ứng trên Amazon S3.
- **ALWAYS:** ALWAYS sử dụng `user_id` làm Partition Key (PK) cho tất cả các bảng DynamoDB để bảo đảm cô lập dữ liệu cá nhân và truy vấn theo người dùng hiệu quả.
- **MUST:** DynamoDB MUST lưu metadata có cấu trúc và các trạng thái nghiệp vụ quan trọng như giao dịch, task, session, lịch sử phân loại, và các mối quan hệ tổng hợp cần truy xuất nhanh.
- **MUST NOT:** Không được lưu trữ dữ liệu lớn hoặc binary data trực tiếp trên DynamoDB nếu mục đích chính là lưu file phương tiện hoặc backup.
- **ALWAYS:** Mỗi S3 object MUST có thông tin metadata hợp lệ (user_id, object_type, created_at, source) để quản lý cleanup, truy xuất và kiểm soát quyền truy cập.
- **MUST:** Kiểm tra hợp lệ và xác thực thông tin khi tạo liên kết giữa DynamoDB item và S3 object key để tránh broken references hoặc dữ liệu chồng chéo giữa người dùng.
- **MUST:** Người dùng hoặc Agent không được sửa trực tiếp dữ liệu tài chính quan trọng nếu chưa đi qua cơ chế validation và xác nhận phù hợp.

### 4. Consequences & Acceptance Criteria (Hệ quả & Tiêu chuẩn nghiệm thu)

**A. Tác động tích cực kỳ vọng**

- Mục tiêu đề xuất: truy vấn dữ liệu giao dịch và task trong DynamoDB có thể giữ ở mức dưới 10 ms trong điều kiện benchmark đã xác định trước.
- Mô hình lưu trữ rõ ràng cho phép tách biệt dữ liệu nhỏ có cấu trúc và file lớn phi cấu trúc, nâng độ quản lý và dễ bảo trì.
- Tăng khả năng mở rộng với lưu lượng truy cập không đồng đều khi user chia theo partition rõ ràng.
- Tối ưu hóa chi phí serverless theo cách phù hợp với ứng dụng AI Agent và tài chính cá nhân.
- Nâng tính tương thích với hạ tầng AWS native, AWS SDK và Bedrock Agent workflows.

**B. Đánh đổi / Nợ kỹ thuật**

- Cần thêm module để quản lý liên kết giữa DynamoDB item và S3 object key, chẳng hạn `src/database/dynamodb_client.py` và các adapter S3 tương ứng.
- Dữ liệu đọc/ghi có thể cần thêm logic “hydrate” từ S3 đến đối tượng ứng dụng và ngược lại, tạo ra độ phức tạp so với trường hợp lưu mọi thứ cùng một nơi.
- Cần thiết lập chính sách cleanup, versioning, lifecycle và quyền truy cập cho S3 object để tránh dư thừa dữ liệu hoặc rò rỉ thông tin cá nhân.
- Nếu hệ thống phát triển thêm nhiều BI queries trên dữ liệu phân tán, sẽ cần thêm data pipeline hoặc query layer ngoài DynamoDB.
- Cần lưu ý rằng không phải mọi trường hợp truy vấn phức tạp đều phù hợp với mô hình NoSQL; cần thêm secondary indexes hoặc materialized views nếu cần.

**C. Tiêu chuẩn nghiệm thu (Acceptance Criteria)**

1. 100% dữ liệu có cấu trúc MUST được lưu trong DynamoDB với schema rõ ràng, `user_id` là partition key và các index cần thiết được định nghĩa nếu cần truy vấn theo thuộc tính khác.
2. Mỗi tài liệu hoặc hóa đơn có file đính kèm MUST được lưu trong S3, trong khi DynamoDB chỉ giữ metadata và link reference.
3. Unit test trong `tests/` MUST bao gồm:
   - tạo, đọc, cập nhật, xóa item trong `Transactions` và `Tasks`;
   - lưu và truy xuất metadata S3;
   - xử lý object không tồn tại, thiếu key, hoặc dữ liệu không hợp lệ.
4. Đánh giá hiệu năng phải xác định benchmark rõ ràng cho latency truy vấn và throughput cho DynamoDB trong các tình huống thực tế.
5. Không được cho phép lưu file lớn hoặc binary data trực tiếp vào item DynamoDB.
6. Kiểm tra quyền truy cập và isolation theo `user_id` phải thành công trước khi triển khai production.

**Lưu ý:** Các chỉ số như latency dưới 10 ms hoặc chi phí gần 0 đều là mục tiêu vận hành đề xuất, không phải kết quả đã xác minh nếu chưa có benchmark thực tế trên dữ liệu production hoặc môi trường test tương đương.

### 5. Revisit Triggers (Điều kiện xem xét lại)

Kiến trúc này cần được xem xét lại khi một trong các điều kiện sau xảy ra:

1. **Yêu cầu analytics phức tạp**
   - Khi cần truy vấn liên bảng hoặc phân tích dữ liệu tổng hợp phức tạp vượt quá khả năng của DynamoDB secondary index, cần đánh giá lại mô hình dữ liệu hoặc bổ sung một tầng analytics riêng.

2. **Chi phí vượt ngưỡng**
   - Khi chi phí đọc/ghi DynamoDB hoặc S3 vượt ngưỡng phê duyệt (ví dụ: trên $20/tháng trong môi trường phát triển hoặc trên ngưỡng đã thống nhất ở production), cần phân tích lại mức độ lưu trữ, index và dữ liệu không cần thiết.

3. **Tăng khối lượng file lớn**
   - Khi số lượng file tài liệu và ảnh chụp hóa đơn tăng mạnh, cần xem xét thêm lifecycle rule, backup policy, compression hoặc chuyển đổi object storage strategy.

4. **Yêu cầu đồng bộ dữ liệu mạnh hơn**
   - Nếu hệ thống cần một model dữ liệu hỗ trợ transactions cross-table hoặc tone of correctness cao hơn so với NoSQL đơn giản, cần đánh giá lại lựa chọn lưu trữ hoặc thêm một tầng dữ liệu hỗ trợ analytics.

5. **Thay đổi hạ tầng AWS**
   - Khi AWS mở ra mô hình lưu trữ hoặc dịch vụ mới giúp tối ưu hóa chi phí, độ trễ hoặc bảo mật hơn so với hybrid storage hiện tại, nhóm kiến trúc cần xem xét lại phương án phù hợp.

---

Nhận xét cuối cùng: Quyết định này xác nhận rằng OnisAgent nên sử dụng mô hình dữ liệu lai: DynamoDB cho dữ liệu có cấu trúc và truy xuất theo người dùng, S3 cho dữ liệu blob lớn như hóa đơn và sao kê. Đây là lựa chọn phù hợp với triết lý serverless, tối ưu hóa chi phí, hỗ trợ Agent memory và dữ liệu giao dịch, đồng thời giảm rủi ro khi lưu file lớn vào NoSQL item. Chúng ta chấp nhận cần bổ sung layer quản lý tham chiếu giữa DynamoDB và S3, nhưng đổi lại có được kiến trúc đơn giản, hiệu quả và dễ mở rộng cho các giai đoạn phát triển tiếp theo của OnisAgent.
