---
id: ADR-0005
timestamp: 2026-10-15T00:00:00Z
status: accepted
deciders: Trịnh Quyết Chiến, Hứa Huỳnh Anh
tags:
  - onisagent
  - voice-first
  - speech-to-text
  - text-to-speech
  - stt
  - tts
  - vietnamese-nlp
  - web-speech-api
  - whisper
  - neural-tts
  - click-to-talk
  - push-to-talk
related_adrs: [ADR-0001, ADR-0002, ADR-0003, ADR-0004]
---

# ADR-0005: Voice-First Two-Way Vietnamese Speech Pipeline (STT/TTS)

> **Y-Statement:** Trong ngữ cảnh OnisAgent giải quyết triệt để rào cản ma sát nhập liệu thủ công (khiến hơn 85% người dùng từ bỏ việc theo dõi tài chính và quản lý công việc), đòi hỏi phương thức giao tiếp rảnh tay (hands-free) tức thì trên Web, Mobile và Smartwatch, chúng tôi quyết định xây dựng **Đường ống Tương tác Giọng nói Hai Chiều Tiếng Việt (Voice-First Two-Way Vietnamese Speech Pipeline)** hỗ trợ linh hoạt 2 chế độ **Click-to-Talk** & **Push-to-Talk**, kết hợp **Web Speech API / Whisper** cho Speech-to-Text (STT) và **Neural TTS** cho Text-to-Speech (TTS), với ngân sách tổng độ trễ dải âm thanh dưới 2 giây (Audio Latency Budget $\le 2$ giây), chấp nhận sự đánh đổi về việc phải xử lý tạp âm môi trường và cấu hình lưu trữ đệm âm thanh tạm thời trên S3/Local cache theo ADR-0003.

---

### 1. Problem Statement & Architectural Intent (Bài toán & Ý tưởng Kiến trúc)

**Bài toán (Context):**
1. **Nghịch lý ma sát nhập liệu (Manual Input Friction):**
   - Để ghi chép một khoản chi tiêu nhỏ hàng ngày (ví dụ: *"uống ly cà phê 35k"* hay *"bát phở 45k"*), người dùng thông thường phải trải qua từ 6 đến 8 thao tác chạm: Mở điện thoại ➔ Mở app ➔ Chọn loại chi ➔ Chọn danh mục ➔ Nhập bàn phím số ➔ Nhập ghi chú ➔ Bấm lưu.
   - Thống kê thực tế cho thấy hơn **85% người dùng bỏ cuộc sau 1–2 tuần** vì sự mệt mỏi và tốn thời gian của quy trình nhập liệu thủ công lặp đi lặp lại.
2. **Hạn chế của các trợ lý giọng nói hiện tại:**
   - Hầu hết các trợ lý giọng nói nước ngoài (Siri, Google Assistant, Alexa) không được tối ưu sâu cho phương ngữ, từ lóng tiếng Việt trong ngữ cảnh tài chính sinh hoạt (như *"35k"*, *"20 củ"*, *"nửa triệu"*, *"tiền trọ"*).
   - Giọng đọc phản hồi thường là giọng máy robot cứng nhắc, thiếu ngữ điệu tự nhiên.
   - Các giải pháp Cloud Voice Streaming liên tục (Continuous Streaming) gây tốn pin nghiêm trọng trên Smartwatch/Mobile, tiềm ẩn rủi ro xâm phạm quyền riêng tư và tạo độ trễ kết nối mạng đứt gãy.

**Mục đích kiến trúc (Intent):**
Thiết lập phương thức tương tác **Voice-First tiếng Việt tự nhiên hai chiều**:
- **Chiều Vào (Inbound Speech):** Cho phép người dùng nói 1 câu tiếng Việt duy nhất (*"Chi 45k ăn phở"*, *"Thêm task hoàn thiện slide họp 9h sáng mai"*), hệ thống tự động nhận dạng, chuẩn hóa số từ tiếng Việt và định tuyến vào lõi AI Dual-Path.
- **Chiều Ra (Outbound Speech):** Phản hồi bằng giọng đọc tiếng Việt mượt mà (Neural TTS) với câu thoại súc tích, ngắn gọn, đi thẳng vào kết quả trong thời gian thực.
- **Tối ưu Độ trễ Toàn trình:** Đảm bảo toàn bộ chu trình từ lúc người dùng dứt lời đến khi nghe thấy giọng đọc phản hồi diễn ra trong vòng **dưới hoặc bằng 2 giây** ($\le 2$ giây).
- **Định tuyến theo ý định:** Sau STT, thao tác lặp lại và rõ ràng (thêm thu chi, tạo task, xem số dư) có thể đi Fast Path; phân tích dòng tiền và dự toán khoản vay đi Reasoning Path. Phép tính tiền tệ ở cả hai luồng luôn dùng Python `Decimal`.

---

### 2. Kiến Trúc Kỹ Thuật: Speech Pipeline & Audio Latency Budget

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               ĐƯỜNG ỐNG TƯƠNG TÁC GIỌNG NÓI HAI CHIỀU (VOICE PIPELINE)                 │
└───────────────────────────────────┬────────────────────────────────────────────────────┘
                                    │
    1. INBOUND SPEECH               ▼
    [ Chế độ Click-to-Talk / Push-to-Talk trên Web / Mobile / Smartwatch ]
                                    │
                                    ▼ (~300 - 500 ms)
    [ Speech-to-Text: Web Speech API / OpenAI Whisper / Local Fast Whisper ]
    • Chuẩn hóa dấu câu tiếng Việt & tiếng lóng ("45k" -> 45.000, "củ" -> triệu)
    • Lưu đệm âm thanh tạm thời vào S3/Local cache (temp_audio/)
                                    │
                                    ▼
    2. COGNITIVE ROUTING            │
    [ 🧭 DECISION ROUTER ] ─────────┼──────────────────────────────┐
                                    ▼ (~5 - 12 ms)                 ▼ (~300 - 800 ms)
                            ⚡ FAST PATH (System 1)        🧠 REASONING (System 2)
                            • Kev Decision Model           • Bedrock / Ollama LLM
                            • Python Decimal Tools         • Grounded Context DB
                                    │                              │
                                    └──────────────┬───────────────┘
                                                   ▼
    3. OUTBOUND SPEECH                             │
    [ Narration Formatter: Rút gọn câu thoại phản hồi <= 2 câu ]
                                    │
                                    ▼ (~300 - 500 ms)
    [ Text-to-Speech: Neural TTS (Edge-TTS / AWS Polly Neural / Web Speech Synthesis) ]
    • Phát âm thanh tiếng Việt tự nhiên qua Loa Web / Mobile / Haptic Watch
                                    │
                                    ▼
    [ TỔNG ĐỘ TRỄ DẢI ÂM THANH TOÀN TRÌNH: <= 2.000 ms (<= 2 giây) ]
```

#### 2.1. Hai Chế Độ Tương Tác Giọng Nói Linh Hoạt
Hệ thống hỗ trợ 2 cơ chế thu âm tùy biến theo thói quen người dùng và đặc thù thiết bị:
1. **Click-to-Talk (Chạm để nói):**
   - Người dùng click vào nút Micro trên Web/Mobile để kích hoạt thu âm.
   - Trình duyệt/App hiển thị thanh sóng âm thanh (Audio Waveform Visualizer) trực quan.
   - Khi người dùng ngừng nói hoặc click lại lần hai, hệ thống tự động chốt câu thoại và kích hoạt xử lý. Phù hợp khi người dùng rảnh tay làm việc trên máy tính.
2. **Push-to-Talk (Nhấn giữ để nói - Bộ đàm):**
   - Người dùng nhấn giữ chuột hoặc chạm giữ màn hình/nút Crown trên Smartwatch để nói; thả tay ra để hoàn tất và gửi câu thoại ngay tức khắc.
   - Tối ưu cho thao tác một tay trên điện thoại di động và đồng hồ thông minh (Wear OS / Apple Watch), kích hoạt kèm phản hồi rung nhẹ (Haptic Feedback) xác nhận.

#### 2.2. Ngân Sách Độ Trễ Toàn Trình (Audio Latency Budget $\le 2$ giây)
Để cuộc đàm thoại diễn ra tự nhiên như người với người, tổng thời gian xử lý âm thanh MUST tuân thủ nghiêm ngặt ngân sách thời gian sau:

| Thành Phần Trong Pipeline | Công Nghệ Thực Thi | Ngân Sách Thời Gian Tối Đa |
|---|---|:---:|
| **1. Thu âm & Nhận diện STT** | Web Speech API (Client) / Fast Whisper | **300 – 500 ms** |
| **2. Phân loại ý định & Tính toán** | Kev System 1 (~5–12 ms) + Python Decimal | **10 – 30 ms** *(Fast Path)* |
| **3. Tổng hợp giọng đọc TTS** | Neural TTS (Edge-TTS / AWS Polly Neural) | **300 – 500 ms** |
| **4. Truyền tải mạng & Phát loa** | WebSocket / Audio Buffer streaming | **200 – 300 ms** |
| **TỔNG ĐỘ TRỄ TOÀN TRÌNH (Fast Path)** | **Toàn bộ chu trình đàm thoại** | **< 1.200 – 1.500 ms** *(SLA: $\le 2.000$ ms)* |

*(Trường hợp truy vấn đi qua Reasoning Path System 2, thời gian sinh văn bản LLM ~500 ms vẫn bảo đảm tổng độ trễ trong ngưỡng SLA $\le 2$ giây).*

#### 2.3. Bộ Xử Lý Ngôn Ngữ Tự Nhiên & Tiếng Lóng Tiếng Việt
Module `src/utils/data_parser.py` được trang bị bộ tiền xử lý chuyên biệt cho thị trường Việt Nam:
- Chuẩn hóa số tiền: *"bốn lăm nghìn"* / *"45k"* $\rightarrow 45.000$, *"hai triệu"* / *"2 củ"* $\rightarrow 2.000.000$, *"năm trăm"* $\rightarrow 500.000$.
- Chuẩn hóa thời gian tương đối: *"hôm nay"*, *"hôm qua"*, *"9 giờ sáng mai"*, *"thứ sáu tuần này"*, *"cuối tháng"*.
- Xóa bỏ từ đệm hội thoại tự nhiên: *"à", "ừm", "nhé", "cho tôi", "giúp mình"*.

#### 2.4. Nguyên Tắc Soạn Lời Thoại Phản Hồi (Narration Voice Directives)
Khác với giao diện chat văn bản, giao diện giọng nói đòi hỏi sự súc tích tuyệt đối để người dùng không phải chờ đợi nghe đọc:
- **Quy tắc 2 câu:** Lời thoại phát ra loa MUST KHÔNG VƯỢT QUÁ 2 câu.
- **Đi thẳng vào kết quả:** Không chào hỏi rườm rà. Bắt buộc nêu rõ hành động đã thực hiện và chỉ số quan trọng nhất:
  - *Ví dụ mẫu 1:* *"Đã ghi nhận khoản chi 45.000 đ cho Ăn phở. Số dư hiện tại là 12.481.880 đ."*
  - *Ví dụ mẫu 2:* *"Đã tạo nhiệm vụ Hoàn thiện slide họp với hạn chót 9 giờ sáng mai."*

---

### 3. Options Considered & Rejection Reasons (Các phương án & Lý do bác bỏ)

| Phương án | Ưu điểm (Pros) | Nhược điểm (Cons) | Lý do bác bỏ / lựa chọn |
|---|---|---|---|
| **Option A: Text-Only (Chỉ dùng bàn phím & biểu mẫu)** | Không phát sinh chi phí audio; không cần xử lý micro hay tiếng ồn. | Giữ nguyên ma sát 6–8 thao tác chạm; hơn 85% người dùng từ bỏ sau 2 tuần; không dùng được khi đang di chuyển hoặc rảnh tay. | **BÁC BỎ:** Đi ngược lại định hướng đột phá trải nghiệm người dùng của OnisAgent. |
| **Option B: Continuous Always-Listening Cloud Streaming** | Người dùng có thể gọi wake-word bất cứ lúc nào (như Siri). | Tốn pin thiết bị nghiêm trọng; lo ngại sâu sắc về bảo mật & quyền riêng tư khi mic luôn mở; chi phí API streaming trên Cloud cực lớn. | **BÁC BỎ:** Gây lo sợ rò rỉ dữ liệu tài chính cho người dùng; không tối ưu cho thiết bị cá nhân. |
| **Option C: Voice-First Click/Push-to-Talk Hybrid Pipeline** | Người dùng chủ động kiểm soát thời điểm thu âm; bảo mật quyền riêng tư; tiết kiệm pin; hỗ trợ tiếng Việt tự nhiên; độ trễ $\le 2$ giây. | Cần xử lý bộ đệm âm thanh tạm thời trên S3/local cache và xử lý lỗi khi trình duyệt không cấp quyền micro. | **ĐƯỢC CHỌN:** Giải pháp lý tưởng, cân bằng trọn vẹn giữa tốc độ, độ chính xác, bảo mật và sự tiện lợi tối đa. |

---

### 4. Directives & Rules (Quy định bắt buộc)

- **MUST (Hỗ trợ 2 chế độ):** Giao diện Web, Mobile và Smartwatch MUST hỗ trợ cả 2 chế độ: Click-to-Talk (bật/tắt) và Push-to-Talk (nhấn giữ).
- **MUST (Audio Latency Budget $\le 2$ giây):** Tổng thời gian từ khi kết thúc thu âm đến khi phát âm thanh phản hồi đầu tiên MUST KHÔNG VƯỢT QUÁ 2.000 ms đối với các tác vụ Fast Path.
- **MUST (Xử lý tiếng lóng tiếng Việt):** Bộ trích xuất ngôn ngữ MUST nhận diện chính xác các cách gọi tiền tệ dân dã thông dụng của người Việt ("k", "củ", "lít", "nghìn", "triệu").
- **MUST NOT (Cấm thoại dài lê thê):** Bản tin âm thanh phản hồi Text-to-Speech MUST NOT dài quá 2 câu. Chi tiết số liệu phân tích dài chỉ hiển thị trên màn hình hiển thị, không đọc hết qua loa.
- **MUST (Tuân thủ ADR-0003 về Temp Audio):** Mọi file âm thanh ghi âm tạm thời gửi lên backend MUST được lưu vào tiền tố `temp_audio/` và tự động kích hoạt S3 Lifecycle Rule xóa vĩnh viễn sau 24–48 giờ.
- **ALWAYS (Fallback mượt mà):** Khi micro không khả dụng, bị chặn quyền truy cập hoặc thiết bị mất kết nối âm thanh, hệ thống ALWAYS tự động chuyển sang chế độ gõ phím / chat text mà không làm gián đoạn phiên làm việc.

---

### 5. Consequences & Acceptance Criteria (Hệ quả & Tiêu chuẩn nghiệm thu)

#### A. Lợi ích đạt được
- **Triệt tiêu ma sát nhập liệu:** Giảm số bước thao tác từ 6–8 bước chạm xuống còn **1 câu nói duy nhất trong 1 giây**.
- **Tăng tỷ lệ giữ chân người dùng:** Khắc phục triệt để tình trạng 85% người dùng từ bỏ ứng dụng quản lý cá nhân sau 1–2 tuần.
- **Trải nghiệm đa nền tảng tối ưu:** Tạo nền tảng đồng nhất cho các giao diện Web Dashboard, ứng dụng Mobile và đồng hồ thông minh (Wear OS / Apple Watch).

#### B. Đánh đổi & Thách thức
- Chất lượng nhận diện phụ thuộc vào micro thiết bị và tiếng ồn môi trường xung quanh.
- Cần cài đặt kiểm soát quyền Micro trên trình duyệt (Browser Permission Handling).

#### C. Tiêu chuẩn nghiệm thu (Acceptance Criteria)
1. **Kiểm tra độ trễ âm thanh:** Benchmark đo đạc thời gian từ lúc dứt câu thoại thu âm đến khi loa phát tiếng đạt trung bình $\le 1.500$ ms trên môi trường thử nghiệm tiêu chuẩn (không bao giờ vượt quá SLA $\le 2$ giây).
2. **Độ chính xác STT Tiếng Việt:** Đạt tỷ lệ trích xuất đúng ý định và số tiền $\ge 90\%$ trên tập 50 câu thoại tiếng Việt mẫu (bao gồm từ lóng "k", "củ", "nửa triệu").
3. **Hoạt động của 2 chế độ tương tác:** Cả hai chế độ Click-to-Talk và Push-to-Talk đều ghi âm và kích hoạt xử lý chính xác trên giao diện UI.
4. **Tự động dọn dẹp Temp Audio:** Kiểm tra trên S3 hoặc local cache xác nhận các file ghi âm tạm thời không còn tồn tại sau 48 giờ.

---

### 6. Revisit Triggers (Điều kiện xem xét lại)

Quyết định kiến trúc này cần được đánh giá lại khi:
1. Công nghệ WebAssembly Whisper On-Device đạt độ trễ $< 150$ ms trực tiếp trên trình duyệt, cho phép loại bỏ hoàn toàn việc truyền file âm thanh lên backend.
2. Tỷ lệ nhận diện sai giọng nói địa phương (Bắc - Trung - Nam) vượt quá 15% trong báo cáo phản hồi người dùng.
3. Xuất hiện tiêu chuẩn Web Audio API mới cho phép streaming song công hai chiều (Full-duplex bidirectional audio) với độ trễ dưới 200 ms.

---

Nhận xét cuối cùng: Tính năng Voice-First với đường ống xử lý hai chiều tiếng Việt siêu tốc là bước nhảy vọt giúp OnisAgent chuyển mình từ một phần mềm quản lý sổ sách thụ động thành một trợ lý AI cá nhân đắc lực, thấu hiểu và gắn bó mật thiết với cuộc sống hàng ngày của người dùng.
