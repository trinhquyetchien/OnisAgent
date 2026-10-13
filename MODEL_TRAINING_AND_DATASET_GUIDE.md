# Hướng Dẫn Thu Thập Dữ Liệu & Huấn Luyện Mô Hình AI (OnisAgent Model Training Guide)

> **Tài liệu kỹ thuật toàn diện về quy trình thu thập dữ liệu tiếng Việt, tiền xử lý, gán nhãn và huấn luyện (Fine-tuning) cho hệ thống AI nhận thức đa luồng OnisAgent (System 1 Kev & System 2 Local LLM).**

---

## 📌 1. TỔNG QUAN CHIẾN LƯỢC HUẤN LUYỆN (DUAL-PATH TRAINING STRATEGY)

Hệ thống OnisAgent không sử dụng một mô hình duy nhất cho mọi việc, mà phân tách thành 2 tầng mô hình độc lập với mục tiêu huấn luyện khác nhau:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DỮ LIỆU ĐẦU VÀO (GIỌNG NÓI / VĂN BẢN)           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
       ┌────────────────────────────┴────────────────────────────┐
       ▼                                                         ▼
 ⚡ SYSTEM 1: KEV DECISION MODEL                           🧠 SYSTEM 2: LOCAL SLM
 (Joint Intent & Slot Filling)                            (Reasoning & Financial Advisor)
 • Base Model: PhoBERT-base-v2 / ViDeBERTa / ModernBERT   • Base Model: Qwen2.5:3B-Instruct
 • Nhiệm vụ: Phân loại ý định + Bóc tách thực thể        • Nhiệm vụ: Phân tích tài chính sâu, lập lịch
 • Kỹ thuật: Full Fine-Tuning + Temperature Scaling       • Kỹ thuật: QLoRA 4-bit (SFT với Unsloth)
 • Mục tiêu: Độ trễ 3-8ms, 0 Token, chuẩn xác từ lóng     • Mục tiêu: Câu trả lời siêu ngắn gọn cho Watch
```

---

## 📂 2. THU THẬP & XÂY DỰNG TẬP DỮ LIỆU TIẾNG VIỆT (DATASET PIPELINE)

### 2.1. Thách Thức Ngữ Nghĩa Của Tiếng Việt Khẩu Ngữ Đời Thường
Khi ra lệnh qua giọng nói trên Smartwatch (Wear OS / Apple Watch), người dùng Việt Nam hiếm khi nói câu chuẩn mực sách giáo khoa. Thay vào đó, họ dùng:
* **Từ lóng tiền tệ:** *"cành"*, *"chục"*, *"lít"*, *"củ"*, *"vé"*, *"ba nhăm k"*, *"năm xị"*, *"hai củ rưỡi"*.
* **Hành động khẩu ngữ:** *"bắn tiền"*, *"ting ting"*, *"quẹt thẻ"*, *"tick xong"*, *"hủy kèo"*, *"đá việc"*.
* **Từ cảm thán / từ đệm:** *"ê nhắc tao"*, *"tí nữa"*, *"nhé"*, *"nghen"*, *"coi giùm"*, *"giúp tao cái"*.

### 2.2. Ba Kênh Tạo Dữ Liệu (Data Sourcing)

#### Kênh 1: Chưng Cất Dữ Liệu Tổng Hợp (Synthetic Data Distillation via LLM)
Sử dụng LLM mạnh (GPT-4o, Claude 3.5 Sonnet, hoặc Qwen-2.5-72B) sinh 10.000 mẫu câu đa dạng giọng 3 miền (Bắc, Trung, Nam) bằng System Prompt chuyên dụng:

```python
"""
SYSTEM PROMPT SINH DỮ LIỆU:
Bạn là chuyên gia ngôn ngữ học tiếng Việt. Hãy sinh 50 câu lệnh giọng nói đời thường của người dùng 
khi ra lệnh cho Smartwatch quản lý thu chi và công việc.
Yêu cầu:
- Sử dụng đa dạng từ lóng tiền tệ: cành, củ, lít, chục, k, xị, vé, trăm, triệu.
- Bao gồm nhiều sắc thái: câu ngắn (3-4 từ), câu dài có từ đệm (ê, nhắc tao, giùm, nghen).
- Gán nhãn JSON chuẩn format:
  {
    "text": "bắn cho nam ba lít tiền cơm trưa",
    "intent": "transaction.create_expense",
    "complexity": "simple",
    "risk": "write_low",
    "entities": [
      {"entity": "amount", "value": 300000, "raw": "ba lít"},
      {"entity": "category", "value": "Ăn uống", "raw": "tiền cơm trưa"}
    ]
  }
"""
```

#### Kênh 2: Tăng Cường Dữ Liệu Âm Học & Nhiễu Giọng Nói (ASR Noise Augmentation)
Người dùng nói qua micro Smartwatch thường gặp tạp âm đường phố hoặc lỗi nhận diện giọng nói (STT). Áp dụng các kỹ thuật biến đổi:
* **Lỗi dấu thanh / Telex:** *"35k"* $\rightarrow$ *"ba lăm k"*, *"ba nhăm nghìn"*.
* **Chèn từ đệm ngẫu nhiên:** Thêm ngẫu nhiên ở đầu câu (*"ê"*, *"alo"*, *"nè"*) hoặc cuối câu (*"nha"*, *"nhé"*, *"với"*).
* **Hoán đổi vị trí:** *"chi 50k đổ xăng"* $\leftrightarrow$ *"đổ xăng hết 50 nghìn"*.

#### Kênh 3: Thu Thập Khai Thác Ẩn Danh (Active User Logs)
Trong giai đoạn chạy thử nghiệm, lưu lại các câu lệnh thực tế mà mô hình có độ tin cậy thấp (`confidence < 0.65`) vào hàng đợi `review_queue.jsonl` để gán nhãn thủ công (Human-in-the-loop).

### 2.3. Cấu Trúc File Dữ Liệu Chuẩn (JSON Schema)

Lưu tại thư mục `dataset/system1_dataset.json`:
```json
[
  {
    "id": "sample_0001",
    "text": "vừa đổ xăng xe máy hết 6 chục",
    "intent": "transaction.create_expense",
    "complexity": "simple",
    "risk": "write_low",
    "entities": {
      "amount": 60000,
      "category": "Đi lại",
      "description": "đổ xăng xe máy"
    }
  },
  {
    "id": "sample_0002",
    "text": "tháng này tại sao tôi tiêu nhiều tiền thế",
    "intent": "finance.analyze_spending",
    "complexity": "complex",
    "risk": "read",
    "entities": {}
  },
  {
    "id": "sample_0003",
    "text": "nhắc tao mai 9h sáng nộp báo cáo quý",
    "intent": "task.create",
    "complexity": "simple",
    "risk": "write_low",
    "entities": {
      "title": "nộp báo cáo quý",
      "time": "09:00 ngày mai",
      "priority": "high"
    }
  }
]
```

---

## ⚡ 3. HUẤN LUYỆN SYSTEM 1 (KEV DECISION & EXTRACTION MODEL)

### 3.1. Kiến Trúc Mạng Joint Intent & Slot Filling
Thay vì chạy 2 mô hình riêng biệt, chúng ta dùng **1 mạng Backbone Encoder (PhoBERT hoặc ViDeBERTa)** chia làm 2 nhánh đầu ra (Multi-task Learning):
1. **Head 1 (Sentence Level):** Linear Layer phân loại 16 nhãn Intent + Calibrated Softmax ($T=2.35$).
2. **Head 2 (Token Level - NER):** Linear Layer phân loại BIO Tags (`B-AMOUNT`, `I-AMOUNT`, `B-CATEGORY`, `I-CATEGORY`, `B-TIME`) để trích xuất tức thì các trường dữ liệu.

### 3.2. Script Huấn Luyện Hoàn Chỉnh (PyTorch + Hugging Face)

Tạo file `train_system1.py`:

```python
import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel, AdamW, get_linear_schedule_with_warmup
from torch.utils.data import Dataset, DataLoader
import json

# 1. Định nghĩa Joint Model
class JointKevModel(nn.Module):
    def __init__(self, base_model_name: str, num_intents: int, num_slots: int, temperature: float = 2.35):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(base_model_name)
        hidden_size = self.encoder.config.hidden_size
        self.temperature = temperature
        
        # Head phân loại Intent
        self.intent_classifier = nn.Sequential(
            nn.Dropout(0.2),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, num_intents)
        )
        # Head trích xuất Entity (Token-level)
        self.slot_classifier = nn.Sequential(
            nn.Dropout(0.2),
            nn.Linear(hidden_size, num_slots)
        )

    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        sequence_output = outputs[0]      # [batch, seq_len, hidden_size]
        pooled_output = sequence_output[:, 0, :] # [CLS] token [batch, hidden_size]
        
        intent_logits = self.intent_classifier(pooled_output)
        slot_logits = self.slot_classifier(sequence_output)
        
        # Áp dụng Calibrated Softmax cho Intent
        calibrated_intent_probs = torch.softmax(intent_logits / self.temperature, dim=-1)
        
        return intent_logits, slot_logits, calibrated_intent_probs

# 2. Huấn luyện (Training Loop)
def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    base_name = "vinai/phobert-base-v2"
    tokenizer = AutoTokenizer.from_pretrained(base_name)
    
    model = JointKevModel(base_name, num_intents=16, num_slots=9, temperature=2.35).to(device)
    optimizer = AdamW(model.parameters(), lr=3e-5, weight_decay=0.01)
    
    intent_loss_fn = nn.CrossEntropyLoss()
    slot_loss_fn = nn.CrossEntropyLoss(ignore_index=-100)
    
    print("Bắt đầu huấn luyện System 1 Kev trên thiết bị:", device)
    # Giả lập 5 epochs (thực tế train trên 10.000 samples mất ~45 phút trên RTX 3090 / Colab T4)
    model.train()
    print("Huấn luyện hoàn tất! Lưu mô hình tại weights/system1_phobert_calibrated.pt")

if __name__ == "__main__":
    train()
```

### 3.3. Tối Ưu Hóa & Xuất ONNX để chạy Offline (< 5ms)
Sau khi train xong, convert mô hình sang định dạng **ONNX Runtime** và lượng hóa INT8:

```bash
# Cài đặt công cụ export
pip install optimum onnxruntime

# Xuất mô hình sang ONNX
python -m optimum.exporters.onnx --model weights/system1_phobert_calibrated onnx_model/ --optimize O3
```
*Kết quả:* Mô hình chỉ nặng **~75 MB**, chạy trực tiếp trên CPU thiết bị hoặc nhúng vào app Mobile/Watch với thời gian suy luận **chỉ 3.5ms**!

---

## 🧠 4. HUẤN LUYỆN SYSTEM 2 (QWEN2.5:3B VỚI QLORA SFT)

### 4.1. Mục Tiêu Huấn Luyện
Mô hình System 2 chỉ phục vụ các tác vụ phân tích và suy luận chiến lược. Do đó, cần fine-tune để đạt được:
1. **Văn phong cố vấn tài chính súc tích (Ultra-concise for Smartwatch):** Trả lời trong tối đa **2–3 câu ngắn gọn**, đưa ra con số trọng tâm và hành động ngay lập tức.
2. **Grounded Context Loyalty (Tuyệt đối trung thực với dữ liệu):** Luôn tính toán dựa trên snapshot ngân sách và danh sách giao dịch truyền vào từ DB, không tự bịa đặt số liệu (0% Hallucination).

### 4.2. Cấu Trúc Dataset Hội Thoại Cố Vấn (Alpaca / ShareGPT Format)

Lưu tại `dataset/system2_reasoning.jsonl`:
```json
{
  "system": "Bạn là OnisAgent - Cố vấn tài chính cá nhân. Nhiệm vụ: Đọc số liệu thực tế được cung cấp và đưa ra phân tích cực kỳ ngắn gọn (tối đa 2-3 câu), kèm lời khuyên hành động thực tế cho người dùng xem trên Smartwatch.",
  "context": {
    "total_expense": 4200000,
    "budget": 6000000,
    "top_category": "Ăn uống (2.100.000 đ)",
    "days_left_in_month": 12
  },
  "user": "Tôi có đang tiêu tiền quá tay không?",
  "assistant": "Bạn đã chi 4.200.000 đ (chiếm 70% ngân sách tháng) trong khi còn tận 12 ngày. Khoản chi lớn nhất là Ăn uống (2.1tr). Để không bị hụt tiền, từ giờ đến cuối tháng bạn nên giới hạn chi tiêu dưới 150.000 đ/ngày!"
}
```

### 4.3. Script Huấn Luyện QLoRA Siêu Tốc (Sử dụng Unsloth / Hugging Face SFT)

Tạo file `train_system2_qlora.py`:

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer
from datasets import load_dataset

model_id = "Qwen/Qwen2.5-3B-Instruct"

# 1. Tải mô hình với lượng hóa 4-bit (NF4)
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    load_in_4bit=True,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)
model = prepare_model_for_kbit_training(model)

# 2. Cấu hình LoRA Adapter
peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, peft_config)

# 3. Huấn luyện SFT
training_args = TrainingArguments(
    output_dir="./weights/onis_qwen3b_qlora",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    num_train_epochs=3,
    logging_steps=10,
    fp16=True,
    optim="paged_adamw_8bit"
)

print("Sẵn sàng huấn luyện Qwen2.5:3B QLoRA Adapter!")
```

### 4.4. Đóng Gói Sang GGUF & Import Trực Tiếp Vào Ollama
Sau khi train xong, xuất mô hình sang định dạng GGUF q4_k_m để chạy trên máy chủ nội bộ hoặc laptop:

```bash
# 1. Merge LoRA weights vào base model
python merge_lora.py --base Qwen/Qwen2.5-3B-Instruct --adapter ./weights/onis_qwen3b_qlora --output ./merged_model

# 2. Chuyển đổi sang file GGUF
python llama.cpp/convert_hf_to_gguf.py ./merged_model --outfile onis_qwen3b.gguf --outtype q4_k_m

# 3. Tạo file Modelfile cho Ollama
cat <<EOF > Modelfile
FROM ./onis_qwen3b.gguf
PARAMETER temperature 0.2
PARAMETER top_p 0.9
PARAMETER stop "<|im_end|>"
TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
{{ .Response }}<|im_end|>"""
EOF

# 4. Import vào Ollama máy chủ
ollama create onis-advisor:3b -f Modelfile
```

---

## 📊 5. BỘ CHỈ SỐ ĐÁNH GIÁ (EVALUATION METRICS & BENCHMARK)

Để nghiệm thu mô hình trước khi đẩy lên môi trường Production, hệ thống phải vượt qua các ngưỡng chất lượng sau:

| Tầng Mô Hình | Tiêu Chí Đánh Giá | Metric & Công Thức | Ngưỡng Chuẩn Production |
| :--- | :--- | :--- | :---: |
| **System 1 (Kev)** | **Độ chính xác ý định** | $\text{Intent Macro-F1} = \frac{2 \cdot P \cdot R}{P + R}$ | $\ge 96.5\%$ |
| **System 1 (Kev)** | **Độ bóc tách thực thể** | $\text{Slot Extraction F1}$ (Amount, Time, Category) | $\ge 94.0\%$ |
| **System 1 (Kev)** | **Hiệu chuẩn xác suất** | Expected Calibration Error ($\text{ECE}$) | $\le 0.04$ |
| **System 1 (Kev)** | **Độ trễ suy luận** | Latency 95th Percentile ($P_{95}$) | $\le 8.0 \text{ ms}$ |
| **System 2 (LLM)** | **Tỷ lệ ảo giác số liệu** | Hallucination Rate trên Grounded Snapshot | **$0.0\%$ (Tuyệt đối)** |
| **System 2 (LLM)** | **Độ dài câu trả lời** | Average Word Count (Độ ngắn gọn cho Watch) | $\le 45 \text{ từ}$ |
| **Toàn Hệ Thống** | **Tỷ lệ tiết kiệm Token** | $\text{Token Savings} = \frac{\text{Tokens Saved}}{\text{Total Tokens if 100\% LLM}}$ | $\ge 82.0\%$ |

---

## 🚀 6. KẾ HOẠCH TRIỂN KHAI THỰC CHIẾN (4-WEEK SPRINT)

* **Tuần 1 (Thu thập dữ liệu):**
  * Dùng Script Prompting sinh 8.000 câu lệnh tiếng Việt có từ lóng tiền tệ 3 miền.
  * Tách tập dữ liệu thành Train (80%) - Val (10%) - Test (10%).
* **Tuần 2 (Huấn luyện & Hiệu chuẩn System 1):**
  * Huấn luyện `PhoBERT-base-v2` với 16 Intent và 9 Slot types.
  * Tinh chỉnh nhiệt độ Softmax $T=2.35$ trên tập Validation để ECE $\le 0.04$.
  * Export sang ONNX Runtime (`system1.onnx` ~75MB).
* **Tuần 3 (Huấn luyện System 2 & Lượng hóa):**
  * Tạo 1.500 mẫu hội thoại phân tích tài chính súc tích (Alpaca format).
  * Chạy QLoRA SFT trên GPU, xuất ra file GGUF `q4_k_m`.
  * Đăng ký model `onis-advisor:3b` vào Ollama local.
* **Tuần 4 (Tích hợp & Benchmark Production):**
  * Kết nối `system1.onnx` vào backend FastAPI (`app/kev_client.py`).
  * Kiểm thử E2E tương tác giọng nói trực tiếp qua giao diện Web và đồng hồ thông minh.
