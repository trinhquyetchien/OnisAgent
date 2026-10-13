# 📚 Thư Viện Tài Liệu Dự Án OnisAgent (Project Documentation)

Toàn bộ tài liệu kỹ thuật, slide thuyết trình, sơ đồ kiến trúc và cẩm nang huấn luyện mô hình của OnisAgent được tập hợp tại đây:

---

## 📑 Danh Mục Tài Liệu

### 1. 🎤 [Slide Trình Chiếu Kỹ Thuật (PRESENTATION_SLIDES.md)](PRESENTATION_SLIDES.md)
* **Mục đích:** Bộ 16 slide thuyết trình chuẩn cấu trúc pitch deck (PowerPoint, Google Slides, Marp, Keynote).
* **Nội dung:**
  * Phần 1: Vấn đề (Dữ liệu phân mảnh, ma sát nhập liệu, bẫy LLM overkill).
  * Phần 2: Tuyên ngôn giải pháp & Lợi thế cạnh tranh vượt trội (Single-Agent Dual-Path).
  * Phần 3: Công nghệ & Kiến trúc (Sơ đồ kiến trúc AI và Sơ đồ Tech Stack chuẩn tỷ lệ 1:1, phân tích kỹ thuật Kev, Ollama, Policy Engine).
  * Phần 4: Hệ sinh thái 22 tính năng nghiệp vụ, kịch bản demo và UI Cyber Dark.

---

### 2. 🧠 [Hướng Dẫn Huấn Luyện AI & Thu Thập Dữ Liệu (MODEL_TRAINING_AND_DATASET_GUIDE.md)](MODEL_TRAINING_AND_DATASET_GUIDE.md)
* **Mục đích:** Cẩm nang toàn diện về quy trình thu thập dữ liệu khẩu ngữ tiếng Việt đời thường và huấn luyện AI.
* **Nội dung:**
  * **System 1 (Kev / PhoBERT / ViDeBERTa):** Huấn luyện Joint Intent Classification (16 nhãn) + BIO Slot Filling (trích xuất tiền tệ, ngày giờ, danh mục), hiệu chuẩn Softmax $T=2.35$, xuất mô hình sang ONNX Runtime (3.5ms, 75MB) chạy offline trên Wear OS / Mobile.
  * **System 2 (Qwen2.5:3B QLoRA SFT):** Tối ưu hóa văn phong cố vấn tài chính siêu ngắn gọn (< 45 từ) cho Smartwatch, triệt tiêu ảo giác số liệu bằng Grounded Context, đóng gói Ollama GGUF Modelfile.
  * Bộ tiêu chí nghiệm thu Production và kế hoạch triển khai 4 tuần.

---

### 3. 🌐 [Bản Đặc Tả Thiết Kế Gốc (OnisAgent_Project_Overview.html)](OnisAgent_Project_Overview.html)
* **Mục đích:** Bản thiết kế nguyên bản dạng HTML tương tác về kiến trúc tổng thể, nguyên lý Single-Agent Dual-Path và cơ chế ra quyết định System 1 / System 2.

---

### 4. 📐 [Sơ Đồ Luồng Quyết Định Draw.io (onisagent_architecture_flow.drawio)](onisagent_architecture_flow.drawio)
* **Mục đích:** File sơ đồ kỹ thuật chi tiết mở bằng [app.diagrams.net](https://app.diagrams.net/) (Draw.io).
* **Nội dung:** Thể hiện luồng rẽ nhánh chi tiết từ người dùng (Mic/Web) qua FastAPI Gateway $\rightarrow$ Decision Router $\rightarrow$ Fast Path (Kev 5ms) vs Reasoning Path (Ollama) $\rightarrow$ Policy Validator $\rightarrow$ Storage.
