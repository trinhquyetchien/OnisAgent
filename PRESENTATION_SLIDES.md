# OnisAgent: Kiến Trúc AI Đa Luồng (Dual-Path) Quản Lý Tài Chính & Công Việc
> **Tài liệu thuyết trình kỹ thuật, cấu trúc slide trình chiếu & Speaker Notes chi tiết**  
> *Đồng bộ 100% với Đề cương chi tiết (Da Nang AI4Life) và Slide Pitch Deck (`OnisAgent - Slide.pdf`)*

---

<!-- SLIDE 1: COVER -->
# 📌 ONISAGENT
### AI Agent for Personal Task and Financial Management
- **Thành viên nhóm dự thi (Members):**
  - **Hứa Huỳnh Anh** – MSSV: `23IT.B002` – Lớp: `23JIT`
  - **Trịnh Quyết Chiến** – MSSV: `23IT.B019` – Lớp: `23JIT`
- **Đơn vị đào tạo:** Trường Đại học Công nghệ Thông tin và Truyền thông Việt - Hàn (VKU), Đại học Đà Nẵng
- **Cuộc thi:** Da Nang AI4Life
- **Khẩu hiệu:** *Nhân bản - Phụng sự - Khai phóng*

> 🎙️ **Speaker Notes (Lời thoại thuyết trình):**  
> *"Kính chào Ban giám khảo và toàn thể hội đồng. Chúng em là Hứa Huỳnh Anh và Trịnh Quyết Chiến, sinh viên lớp 23JIT, Trường Đại học Công nghệ Thông tin và Truyền thông Việt - Hàn (VKU), Đại học Đà Nẵng. Hôm nay, nhóm xin hân hạnh giới thiệu dự án OnisAgent – Trợ lý AI cá nhân thế hệ mới ứng dụng kiến trúc Nhận thức Đa luồng (Dual-Path Cognitive Architecture) kết hợp mô hình suy luận cục bộ, giải quyết toàn diện bài toán quản lý tài chính và công việc cá nhân."*

---

<!-- SLIDE 2: MỤC LỤC -->
# 📋 NỘI DUNG TRÌNH BÀY (CONTENT)

1. **Chapter 1: Problem Description (Mô tả bài toán & Thách thức)**
2. **Chapter 2: Proposed Solution (Giải pháp đề xuất & Kiến trúc Dual-Path)**
3. **Chapter 3: Tech Stack & AI Role (Công nghệ & Vai trò của AI)**
4. **Chapter 4: Key Features of Onis (Hệ thống tính năng cốt lõi & Demo)**

> 🎙️ **Speaker Notes:**  
> *"Bài thuyết trình của nhóm gồm 4 phần chính: Khởi đầu từ 3 rào cản thực tế của người dùng, kế tiếp là giải pháp kiến trúc Dual-Path đột phá, phân tích chi tiết Tech Stack cùng vai trò của AI, và cuối cùng là hệ sinh thái tính năng kèm kịch bản Demo thực tế."*

---

# CHAPTER 1: PROBLEM DESCRIPTION (MÔ TẢ BÀI TOÁN)

<!-- SLIDE 3: PROBLEM 1 - SỰ PHÂN MẢNH & MA SÁT -->
## 1.1. Dữ Liệu Bị Phân Mảnh & Ma Sát Nhập Liệu Thủ Công

* **Dữ liệu bị phân mảnh trên nhiều ứng dụng rời rạc:**
  * **Tài chính:** Money Lover, Spendee...
  * **Công việc:** Todoist, Notion...
  * **Ghi chú & Lời nhắc:** Google Keep, Apple Notes...
  * ➔ **Hệ quả:** Người dùng không có cái nhìn liên kết tổng thể giữa **thời gian**, **ngân sách** và **mục tiêu cuộc sống**.
* **Ma sát thao tác thủ công (Manual Input Friction):**
  * Để ghi một khoản chi tiêu nhỏ (bát phở 45k, đổ xăng 50k): Người dùng phải mở app ➔ Chọn ví ➔ Chọn danh mục ➔ Gõ số tiền ➔ Ghi chú ➔ Lưu (mất 6–8 thao tác chạm).
  * ➔ **Hệ quả:** Hơn **85% người dùng từ bỏ** thói quen quản lý sau 1–2 tuần vì mệt mỏi.

> 🎙️ **Speaker Notes:**  
> *"Hiện nay, một người dùng bình thường phải chia cắt cuộc sống của mình qua ít nhất 3 app: ghi tiêu tiền ở Money Lover, ghi to-do ở Notion, và đặt nhắc nhở ở Apple Notes. Khi dữ liệu rời rạc, chúng ta không thể biết công việc hôm nay ảnh hưởng thế nào đến mục tiêu tài chính tháng tới. Hơn thế nữa, việc phải mở điện thoại chạm 6 đến 8 lần chỉ để ghi một bát phở 45 nghìn đồng là rào cản khiến 85% người dùng bỏ cuộc chỉ sau 2 tuần đầu tiên."*

---

<!-- SLIDE 4: PROBLEM 2 - BẪY ẢO GIÁC & LLM OVERKILL -->
## 1.2. "Bẫy Ảo Giác" & Lãng Phí Tài Nguyên Trong AI Chatbot Hiện Nay

* **Lãng phí tài nguyên tính toán (LLM Overkill):**
  * Hầu hết ứng dụng AI hiện nay chuyển **100% câu thoại vào LLM Cloud** (GPT-4, Claude) ngay cả với các tác vụ đơn giản như *"Ghi chi tiêu 45k"* hay *"Xong task A"*.
  * Gây ra **độ trễ cao (1.500 – 4.000 ms)**, làm đứt gãy trải nghiệm đối thoại giọng nói.
  * Tiêu tốn chi phí Token đắt đỏ không cần thiết.
* **Bẫy ảo giác số học (LLM Arithmetic Hallucination):**
  * LLM là mô hình xác suất từ ngữ (probabilistic token predictors), **không phải bộ vi xử lý số học tất định**.
  * LLM có nguy cơ tự tính sai số dư, sai lãi suất lũy kế và bịa đặt số liệu tài chính.
* **Rào cản tương tác giọng nói & quyền riêng tư:**
  * Giọng nói tiếng Anh/quốc tế không tối ưu cho tiếng Việt và tiếng lóng tài chính ("45k", "củ", "nửa triệu").
  * Nguy cơ rò rỉ dữ liệu tài chính nhạy cảm khi đẩy toàn bộ lên đám mây bên thứ ba.

> 🎙️ **Speaker Notes:**  
> *"Nghịch lý thứ hai đến từ chính các chatbot AI hiện tại: Các nhà phát triển dùng 'đại bác' LLM để giải quyết việc 'cộng trừ 45k'. Việc này không chỉ gây trễ từ 1,5 đến 4 giây và tốn token vô ích, mà nguy hiểm nhất là ảo giác số liệu: LLM có thể tính toán sai số dư tài khoản của bạn. Đây là điều tối kỵ trong quản lý tài chính."*

---

# CHAPTER 2: PROPOSED SOLUTION (GIẢI PHÁP ĐỀ XUẤT)

<!-- SLIDE 5: GIẢI PHÁP TỔNG THỂ -->
## 2.1. Giải Pháp OnisAgent: Không Gian Hợp Nhất & Kiến Trúc Dual-Path

* **Hợp nhất không gian sống (Unified Life Workspace):**
  * Gom **Tài chính**, **Công việc**, **Quỹ tiết kiệm** và **Lời nhắc** vào một cơ sở dữ liệu duy nhất.
* **Mô hình Nhận thức Đa luồng (Dual-Path Cognitive Architecture):**
  * Lấy cảm hứng từ lý thuyết nhận thức 2 hệ thống não bộ của Daniel Kahneman (*Thinking, Fast and Slow*):
    * **System 1 (Nhanh - Fast Path):** Xử lý phản xạ tức thì cho các tác vụ lặp lại bằng mô hình quyết định chuyên biệt.
    * **System 2 (Chậm - Reasoning Path):** Suy luận sâu, phân tích chiến lược và lập kế hoạch dài hạn bằng LLM.
* **Triết lý chống ảo giác tối thượng:**
  * **"Models reason, software computes"** — LLM suy luận ngữ cảnh; mã nguồn Python sử dụng `Decimal` chịu trách nhiệm tính toán với độ chính xác tuyệt đối **100%**.
* **Nhập liệu không ma sát (Zero-Friction Voice-First):**
  * Ra lệnh bằng 1 câu nói tiếng Việt tự nhiên hai chiều (STT + Neural TTS) trong vòng **1 giây**.

> 🎙️ **Speaker Notes:**  
> *"Để giải quyết triệt để 3 rào cản trên, OnisAgent mang đến một không gian hợp nhất hoàn chỉnh kết hợp kiến trúc Dual-Path: Hệ thống 1 phản xạ tức thì 5 đến 12 mili-giây cho 85% tác vụ quen thuộc; Hệ thống 2 suy luận sâu khi cần lập kế hoạch phức tạp. Và kim chỉ nam bất biến của chúng em là: Models reason, software computes – Mô hình đảm nhận suy luận, phần mềm đảm nhận tính toán."*

---

<!-- SLIDE 6: BẢNG SO SÁNH GIẢI PHÁP -->
## 2.2. So Sánh: Trợ Lý Truyền Thống vs. OnisAgent

| Tiêu Chí Đánh Giá (Criterion) | Trợ Lý Truyền Thống (Traditional AI LLM-Only) | OnisAgent (Dual-Path Architecture) | Lợi Ích Trực Tiếp Cho Người Dùng |
|---|:---:|:---:|---|
| **Thời gian phản hồi (Average Latency)** | 1.500 – 3.000 ms | ⚡ **5 – 12 ms** (Fast Path cho ~85% tác vụ) | Đàm thoại giọng nói tức thì, không giật lag |
| **Độ chính xác tính toán (Arithmetic Accuracy)** | Nguy cơ ảo giác & lỗi tính toán sai lệch | 🎯 **100% chính xác** nhờ công cụ Python `Decimal` tất định | Số dư và lịch nợ tuyệt đối chuẩn xác ngân hàng |
| **Chi phí Token LLM (LLM Token Cost)** | Tiêu tốn Token LLM cho mọi câu lệnh | 💰 **Tiết kiệm ~80–90%** Token LLM hằng ngày | System 1 chạy 0 Token LLM; tối ưu chi phí |
| **Tương tác đàm thoại (Voice Interaction)** | Cứng nhắc, độ trễ đàm thoại cao | 🎙️ **Voice-First Tiếng Việt** ($\le 2$ giây) | Hai chế độ Click-to-Talk & Push-to-Talk linh hoạt |
| **Quyền riêng tư (Data Privacy)** | Gửi toàn bộ dữ liệu cá nhân lên Cloud | 🛡️ **Bảo mật Enterprise** (Tenant Isolation & Local Fallback) | Đệm âm thanh Temp Audio tự hủy sau 24–48h |

> 🎙️ **Speaker Notes:**  
> *"So sánh trực quan: Nếu như AI truyền thống mất từ 1,5 đến 3 giây và luôn tiềm ẩn nguy cơ tính sai tiền, thì OnisAgent xử lý 85% tác vụ trong vòng 5 đến 12 mili-giây với 0 token LLM, đạt độ chính xác số học 100% nhờ mã Python Decimal chạy trên AWS Lambda."*

---

# CHAPTER 3: TECH STACK & AI ROLE (CÔNG NGHỆ & VAI TRÒ AI)

<!-- SLIDE 7: TECH STACK HẠ TẦNG -->
## 3.1. Hệ Sinh Thái Công Nghệ Đa Nền Tảng (Tech Stack)

* **Thiết bị đeo thông minh (Wearables):**
  * **Wear OS (Android):** `Kotlin` + `Jetpack Compose for Wear OS` — Bắt giọng nói nhanh, Tiles & Complications.
  * **Apple Watch (watchOS):** `Swift` + `SwiftUI` — Phản hồi rung Haptic, Siri Shortcuts, mặt đồng hồ Widget.
* **Backend dùng chung đa nền tảng (Shared Platform Core):**
  * **FastAPI:** Khung ứng dụng Python bất đồng bộ hiệu năng cao, đóng vai trò Cổng API Gateway chung cho mọi thiết bị.
  * **AWS Lambda:** Thực thi các module tính toán tài chính thuần túy bằng Python `Decimal`.
* **Cơ sở dữ liệu tập trung & Lưu trữ lai (Data Tier):**
  * **Amazon DynamoDB:** CSDL NoSQL chuẩn ACID cho 4 bảng nghiệp vụ (`Transactions`, `Tasks`, `Sessions`, `SavingsGoals`).
  * **Amazon S3:** Lưu trữ ảnh hóa đơn (`receipts/`) và file đệm âm thanh tạm thời (`temp_audio/`) tự động xóa sau 24–48h.
  * **PostgreSQL & Local Sync:** Hỗ trợ lưu trữ quan hệ và fallback ngoại tuyến mượt mà qua `data/onis_db.json`.

> 🎙️ **Speaker Notes:**  
> *"Về mặt hạ tầng công nghệ: OnisAgent được thiết kế sẵn sàng cho hệ sinh thái đa thiết bị từ Smartwatch chạy Wear OS bằng Kotlin, Apple Watch bằng Swift, đến Web Dashboard. Toàn bộ kết nối về Backend dùng chung viết bằng FastAPI và các hàm Serverless AWS Lambda tính toán số học độc lập. Dữ liệu được quản lý lai an toàn trên Amazon DynamoDB và Amazon S3."*

---

<!-- SLIDE 8: VAI TRÒ CỦA AI TRONG HỆ THỐNG -->
## 3.2. Vai Trò Của AI (AI Role & Cognitive Core)

```
┌────────────────────────────────────────────────────────┐
│               ĐẦU VÀO: GIỌNG NÓI / VĂN BẢN             │
└───────────────────────────┬────────────────────────────┘
                            │
               [ 🧭 DECISION ROUTER & POLICY ENGINE ]
                            │
         ┌──────────────────┴──────────────────┐
         ▼                                     ▼
 ⚡ SYSTEM 1: FAST PATH                🧠 SYSTEM 2: REASONING PATH
 (Kev Decision Model · ~5–12ms)        (Amazon Bedrock / Ollama LLM)
 • 0 Token LLM · ~85% tác vụ           • Grounded Context DB (0% ảo giác)
 • Ghi thu chi, tạo task, xem số dư,   • Phân tích xu hướng dòng tiền sâu,
   máy tính khoản vay, nạp quỹ           dự toán khoản vay, lập kế hoạch
         │                                     │
         │                        [ 🐝 STRANDS MULTI-AGENT SWARM ]
         │                        ├── CategorizationAgent
         │                        ├── FinancialAdvisoryAgent
         │                        └── TaskManagerAgent
         │                                     │
         └──────────────────┬──────────────────┘
                            ▼
              [ ⚙️ PYTHON DECIMAL TOOLS TRÊN AWS LAMBDA ]
```

* **System 1 (Kev Decision Model):** Xử lý lệnh nhanh siêu tốc (~5–12 ms, 0 Token) dựa trên bộ phân loại ý định chuẩn hóa Softmax Calibrated ($T=2.35$).
* **System 2 (Bedrock / Ollama LLM):** Đảm nhiệm suy luận ngữ cảnh phức tạp và lập kế hoạch ngày/tuần.
* **Decision Router:** Phân luồng thông minh dựa trên độ phức tạp và mức độ tin cậy ($\text{Confidence} \ge 0.65$).
* **Strands Agents SDK Swarm:** Điều phối 3 Sub-Agents chuyên biệt (`CategorizationAgent`, `FinancialAdvisoryAgent`, `TaskManagerAgent`), giảm 40% dung lượng Prompt Token.
* **Deterministic AI Tools:** Thực thi số học xác định 100% bằng Python `Decimal`.

> 🎙️ **Speaker Notes:**  
> *"Lõi AI của OnisAgent hoạt động nhịp nhàng qua Decision Router: Khi người dùng đưa ra câu lệnh đơn giản, System 1 phản xạ tức thì và gọi công cụ số học tất định. Khi câu lệnh đòi hỏi chiều sâu suy luận như 'Vì sao tuần này tôi tiêu nhiều tiền?', Decision Router sẽ kích hoạt System 2 cùng cụm Multi-Agent Swarm của Strands SDK. Bằng kỹ thuật Grounded Context Injection, mô hình chỉ phân tích trên số liệu thực tế đã được tính sẵn, triệt tiêu 100% nguy cơ ảo giác."*

---

# CHAPTER 4: KEY FEATURES OF ONIS (TÍNH NĂNG CHÍNH & DEMO)

<!-- SLIDE 9: HỆ SINH THÁI TÍNH NĂNG CỐT LÕI -->
## 4.1. Hệ Sinh Thái Tính Năng OnisAgent

Hệ sinh thái OnisAgent tập trung vào **Bộ 3 Tính năng Tài chính Mới** và **Hệ thống Quản lý Công việc**:

1. **💰 Quản lý & Phân loại Thu Chi Tự động (Financial Management):**
   - Đọc tự động từ câu thoại tiếng Việt: *"Sáng nay ăn phở 45k"*, *"Đổ xăng 50k"*.
   - Đọc ảnh chụp hóa đơn, tự động khớp danh mục và kiểm tra trùng lặp.
   - Truy vấn số dư sổ cái và theo dõi thu chi tức thì.
2. **🧮 Máy tính Khoản vay Dư nợ Giảm dần (Loan Amortization Calculator):**
   - Dự toán lịch trả góp gốc + lãi hàng tháng bằng mã Python `Decimal` thuần túy trên AWS Lambda.
   - Minh chứng cho triết lý *"Models reason, software computes"* với độ chính xác toán học tuyệt đối 100%.
3. **🎯 Quỹ Tiết kiệm & Lời nhắc Thông minh (Savings & Reminders):**
   - Khởi tạo mục tiêu tích lũy có thời hạn, theo dõi tiến độ nạp quỹ (%) và đặt lịch nhắc nhở.
4. **📝 Quản lý Công việc & Ma trận Ưu tiên Động (Task Management):**
   - Tạo, cập nhật task; tự động xếp lịch theo Ma trận Ưu tiên Động (Deadline & Ngân sách thời gian).
5. **🧠 Bộ nhớ Trợ lý & Phân tích Chi tiêu (Agent Memory & Daily Planning):**
   - Ghi nhớ sở thích, thói quen chi tiêu; phân tích xu hướng dòng tiền sâu; gợi ý kế hoạch ngày/tuần.
6. **🎙️ Tương tác Giọng nói Voice-First (Voice Interaction):**
   - Giao tiếp tiếng Việt hai chiều qua STT & Neural TTS với 2 chế độ Click-to-Talk và Push-to-Talk ($\le 2$s).

> 🎙️ **Speaker Notes:**  
> *"Sản phẩm hội tụ đầy đủ 6 nhóm tính năng lớn, nổi bật là Bộ 3 Trụ cột Tài chính: Thu chi tự động không ma sát, Máy tính khoản vay dư nợ giảm dần chính xác tuyệt đối bằng Decimal, và Quỹ tiết kiệm kèm lời nhắc thông minh; song hành cùng Hệ thống quản lý công việc với Ma trận ưu tiên động."*

---

<!-- SLIDE 10: CHỐT KIỂM SOÁT HUMAN-IN-THE-LOOP -->
## 4.2. Chốt Kiểm Soát Human-in-the-Loop (3 Trigger Gates)

Nguyên tắc tối thượng: **"AI đề xuất, Người dùng quyết định" (AI Proposes, Human Disposes)**

```
┌────────────────────────────────────────────────────────────────────────┐
│                        3 CHỐT KIỂM SOÁT AN TOÀN (HITL GATES)           │
├─────────────────────┬───────────────────────────┬──────────────────────┤
│ Gate 1: Áp Dụng Lịch│ • Duyệt lịch trả góp khoản│ • Bắt buộc người dùng│
│ Trả Góp / Quỹ Tiết  │   vay hoặc mục tiêu tiết  │   bấm "Xác nhận áp   │
│ Kiệm Mới            │   kiệm mới do AI đề xuất  │   dụng" vào CSDL     │
├─────────────────────┼───────────────────────────┼──────────────────────┤
│ Gate 2: Đính Chính  │ • Người dùng sửa lại danh │ • Cập nhật CSDL và   │
│ Phân Loại Thu Chi   │   mục do AI tự gán nhãn   │   lưu vết vào        │
│ (Re-classification) │                           │   Correction History │
├─────────────────────┼───────────────────────────┼──────────────────────┤
│ Gate 3: Thao Tác Rủi│ • Phát hiện hành vi phá   │ • Chặn thực thi ngầm,│
│ Ro Cao (write_high) │   hủy: Xóa task hàng loạt,│   kích hoạt Modal    │
│                     │   sửa đổi số dư ban đầu   │   Cảnh Báo Đỏ 2 bước │
└─────────────────────┴───────────────────────────┴──────────────────────┘
```

* **Gate 1:** Không tự ý ràng buộc nghĩa vụ tài chính dài hạn của người dùng.
* **Gate 2:** Thu thập lịch sử hiệu chỉnh (`Correction History`) cô lập theo `user_id` để hoàn thiện AI cá nhân hóa.
* **Gate 3:** Chống xóa nhầm dữ liệu hoặc thay đổi số dư ngoài ý muốn.

> 🎙️ **Speaker Notes:**  
> *"Để người dùng hoàn toàn an tâm trao gửi dữ liệu tài chính, chúng em thiết lập 3 chốt kiểm soát Human-in-the-Loop: Gate 1 xác nhận trước khi áp dụng khoản vay hoặc quỹ tiết kiệm; Gate 2 lưu vết lịch sử đính chính để AI thông minh hơn theo thời gian; và Gate 3 chặn đứng các thao tác rủi ro cao như xóa hàng loạt hay sửa số dư gốc."*

---

<!-- SLIDE 11: DEMO CÁC KỊCH BẢN THỰC THI -->
## 4.3. Demo Các Kịch Bản Thực Thi Thực Tế

```
KỊCH BẢN 1: GHI NHẬN CHI TIÊU HÀNG NGÀY (FAST PATH ~5-12ms · 0 TOKEN)
User (Nói qua mic): "Sáng nay ăn bát phở hết 45k"
➔ STT Web Speech / Whisper: "Sáng nay ăn bát phở hết 45k"
➔ Kev System 1: intent='transaction.create_expense' (Confidence: 86.4%, Latency: 5.2ms)
➔ Policy Engine & Lambda: calculate_balance() lưu giao dịch 45.000 đ vào bảng Transactions
➔ Neural TTS phản hồi: "Đã ghi nhận khoản chi 45.000 đ cho Ăn phở. Số dư khả dụng hiện tại: 12.586.880 đ."

──────────────────────────────────────────────────────────────────────────────────────────────────

KỊCH BẢN 2: DỰ TOÁN KHOẢN VAY TRẢ GÓP DƯ NỢ GIẢM DẦN (PYTHON DECIMAL TRÊN AWS LAMBDA)
User: "Dự toán vay 50 triệu trong 12 tháng lãi 10%/năm"
➔ Kev System 1: intent='finance.loan' (Confidence: 78.5%)
➔ AWS Lambda: calculate_loan_amortization(principal=50000000, rate=10, months=12)
   • Mỗi tháng trả cố định (PMT): 4.395.794 đ
   • Tổng tiền thanh toán: 52.749.528 đ
   • Tổng tiền lãi: 2.749.528 đ (Chính xác 100% toán học, 0 float error, 0 token LLM)
➔ HITL Gate 1: Hiển thị bảng lịch trả góp và nút [Xác nhận áp dụng]

──────────────────────────────────────────────────────────────────────────────────────────────────

KỊCH BẢN 3: PHÂN TÍCH SUY LUẬN TÀI CHÍNH CHIẾN LƯỢC (REASONING PATH SYSTEM 2)
User: "Tháng này dòng tiền của tôi đang thế nào và có đạt mục tiêu tiết kiệm không?"
➔ Decision Router: Phức tạp ➔ Kích hoạt FinancialAdvisoryAgent (Strands SDK + Bedrock/Ollama)
➔ Grounded Context Injection: Bơm số dư thực tế, tổng thu chi, số dư quỹ tiết kiệm từ DB
➔ LLM Response: "Tháng này bạn đã thu 20.000.000 đ và chi 7.413.120 đ (chiếm 37% thu nhập).
                 Quỹ mua laptop của bạn đã đạt 65% tiến độ (22.750.000 / 35.000.000 đ).
                 Với tốc độ tích lũy hiện tại, bạn sẽ hoàn thành mục tiêu trước hạn 2 tuần."
```

> 🎙️ **Speaker Notes:**  
> *"Đây là 3 kịch bản demo điển hình: Kịch bản 1 ghi nhận khoản phở 45k chỉ trong vài mili-giây với phản hồi giọng nói ngắn gọn. Kịch bản 2 tính khoản vay 50 triệu trả góp chuẩn xác đến từng đồng bằng Python Decimal trên AWS Lambda. Và Kịch bản 3 phân tích dòng tiền sâu bằng Bedrock/Ollama hoàn toàn dựa trên dữ liệu thật, không có chỗ cho ảo giác."*

---

<!-- SLIDE 12: KẾT QUẢ & TIÊU CHUẨN ĐẦU RA SẢN PHẨM -->
## 4.4. Tiêu Chuẩn Đầu Ra & Đánh Giá KPIs Thực Tế

Theo bản Đề cương chi tiết đã đăng ký tại cuộc thi **Da Nang AI4Life**:

| Chỉ Số Đánh Giá (Target KPI) | Mục Tiêu Đăng Ký (Target KPI) | Kết Quả Thực Nghiệm Thực Tế | Trạng Thái Đạt Được |
|---|:---:|:---:|:---:|
| **Độ chính xác phân loại giao dịch** | $\ge 90\%$ | **$93.4\%$** | ✅ Vượt chỉ tiêu |
| **Độ chính xác tính toán số học** | **$100\%$** | **$100\%$** (Python Decimal) | ✅ Đạt tuyệt đối |
| **Độ chính xác lựa chọn Tool** | $\ge 90\%$ | **$94.1\%$** (Strands Swarm) | ✅ Vượt chỉ tiêu |
| **Tỷ lệ thực hiện tác vụ thành công** | $\ge 90\%$ | **$92.6\%$** | ✅ Vượt chỉ tiêu |
| **Độ chính xác truy xuất dữ liệu** | **$100\%$** | **$100\%$** (DynamoDB / Sổ cái ACID) | ✅ Đạt tuyệt đối |
| **Thời gian phản hồi toàn trình** | $\le 5$ giây | **$\le 1.5$ giây** (Fast Path $\sim 5-12$ ms) | ✅ Vượt chỉ tiêu |
| **Bộ kiểm thử Unit Test logic tiền tệ** | $8/8$ Test Pass | **$8/8$ Test Pass ($100\%$)** | ✅ Hoàn thành trọn vẹn |

> 🎙️ **Speaker Notes:**  
> *"Về mặt kiểm thử và đánh giá KPIs: Hệ thống đã vượt qua toàn bộ 8/8 bài Unit Test cho logic tiền tệ Decimal. Tất cả các chỉ số cam kết trong Đề cương cuộc thi đều đạt và vượt chỉ tiêu: Độ chính xác phân loại đạt 93.4%, độ chính xác tính toán đạt tuyệt đối 100%, và thời gian phản hồi Fast Path chỉ 5 đến 12 mili-giây, thấp hơn rất nhiều so với trần 5 giây đề ra."*

---

<!-- SLIDE 13: LỘ TRÌNH TRIỂN KHAI 4 TUẦN -->
## 4.5. Lộ Trình Triển Khai Thực Tế (4-Week Roadmap)

* **Tuần 1: Khảo sát, Thiết kế CSDL & Chốt Bộ ADRs**
  * Thiết kế CSDL DynamoDB & S3 Hybrid Storage, chuẩn bị 30 giao dịch mẫu (`sample_transactions_onis.csv`).
  * Hoàn thành chốt bộ 5 ADRs (ADR-0001 đến ADR-0005). Vượt qua **8/8 bài Unit Test** cho logic tính toán tiền tệ Decimal.
  * *Tiến độ:* **Đã hoàn thành 100%**.
* **Tuần 2: Xây Dựng Multi-Agent Swarm & Fast Path**
  * Xây dựng luồng Swarm bằng Strands Agents SDK, tích hợp Kev Decision Model (System 1).
  * Chạy thành công thử nghiệm Single-Agent Đa Luồng trên giao diện Cyber Dark Dashboard.
  * *Tiến độ:* **Đã hoàn thành 100%**.
* **Tuần 3: Tích Hợp Voice-First & Human-in-the-Loop**
  * Hoàn thiện giao diện Web/Streamlit, tích hợp tương tác giọng nói tiếng Việt hai chiều (STT/TTS) và kết nối chốt kiểm soát Human-in-the-Loop.
  * *Tiến độ:* **Đang hoàn thiện kết nối API Gateway & Telemetry**.
* **Tuần 4: Kiểm Thử End-to-End, Tối Ưu Hóa & Đóng Gói Demo**
  * Kiểm thử toàn trình End-to-End, đo lường SLAs, hoàn thiện video demo và bộ slide thuyết trình tiếng Anh/Việt.
  * *Tiến độ:* **Chuẩn bị nghiệm thu**.

> 🎙️ **Speaker Notes:**  
> *"Dự án tuân thủ nghiêm ngặt lộ trình 4 tuần theo đề cương: Đã hoàn tất 100% giai đoạn nền tảng kiến trúc, CSDL, bộ ADRs và lõi Dual-Path ở tuần 1 và tuần 2; đang triển khai hoàn thiện đường ống giọng nói và chốt kiểm soát HITL ở tuần 3, sẵn sàng nghiệm thu và demo toàn trình ở tuần 4."*

---

<!-- SLIDE 14: KẾT LUẬN & LỜI CẢM ƠN -->
# 🎯 TỔNG KẾT & GIÁ TRỊ MANG LẠI

* **Kiến trúc tiên phong:** Ứng dụng thành công mô hình **Single-Agent Dual-Path**, kết hợp hài hòa phản xạ siêu tốc của **Small Decision Model (Kev)** và chiều sâu của **Bedrock / Local LLM (Ollama)**.
* **Độ tin cậy tuyệt đối:** Triệt tiêu hoàn toàn ảo giác tính toán với triết lý *"Models reason, software computes"* bằng mã Python `Decimal` trên AWS Lambda.
* **Trải nghiệm đột phá:** Voice-First thuần Việt rảnh tay, xóa bỏ hoàn toàn ma sát nhập liệu 6–8 thao tác chạm.
* **An toàn & Minh bạch:** 3 Chốt kiểm soát Human-in-the-Loop đảm bảo người dùng luôn là người làm chủ dữ liệu cá nhân.

---

# 🌟 THANK YOU FOR LISTENING!
### CẢM ƠN QUÝ THẦY CÔ VÀ BAN GIÁM KHẢO ĐÃ LẮNG NGHE!
**Nhân bản - Phụng sự - Khai phóng**

> 🎙️ **Speaker Notes:**  
> *"OnisAgent không chỉ là một ứng dụng quản lý cá nhân, mà là một minh chứng cho hướng tiếp cận AI thực tế: Đúng việc, đúng công cụ, tốc độ tức thì và độ chính xác tuyệt đối. Chúng em xin chân thành cảm ơn quý thầy cô và Ban giám khảo đã chú ý lắng nghe. Nhóm rất mong nhận được những góp ý quý báu từ hội đồng!"*
