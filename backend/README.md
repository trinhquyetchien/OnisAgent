# OnisAgent - Backend Service (FastAPI)

Hạ tầng máy chủ độc lập cung cấp toàn bộ API Gateway, điều phối mô hình AI Dual-Path (System 1 Kev & System 2 Ollama), xử lý logic tài chính và lưu trữ dữ liệu.

## Cấu Trúc Thư Mục
```
backend/
├── app/
│   ├── main.py           # FastAPI entrypoint, router và middleware CORS
│   ├── config.py         # Cấu hình môi trường (Kev, Ollama, DB)
│   ├── router.py         # Lõi điều phối Dual-Path & Policy Engine
│   ├── kev_client.py     # Giao tiếp với System 1 Kev Decision Model
│   ├── ollama_client.py  # Giao tiếp với Local LLM (qwen2.5:3b)
│   ├── tools.py          # 22 công cụ xử lý nghiệp vụ tài chính & công việc
│   └── db.py             # Lớp truy xuất cơ sở dữ liệu
├── data/
│   └── onis_db.json      # Sổ cái lưu trữ dữ liệu
├── requirements.txt      # Thư viện phụ thuộc
└── run_backend.sh        # Script khởi chạy độc lập
```

## Khởi Chạy Backend Độc Lập
```bash
# Chạy mặc định trên cổng 8000
./backend/run_backend.sh 8000

# Hoặc dùng uvicorn trực tiếp
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```

Backend đã kích hoạt sẵn **CORS Middleware** (`allow_origins=["*"]`), cho phép các ứng dụng Frontend (Web, Mobile, Smartwatch) kết nối từ bất kỳ domain hoặc cổng nào.
