# Onis – Trợ lý AI quản lý dòng tiền

Onis là bộ khung ứng dụng Python gồm giao diện Streamlit, các agent dùng Strands Agents SDK/Amazon Bedrock, công cụ tính toán tài chính và lớp lưu trữ local hoặc DynamoDB.

## Bắt đầu nhanh

Yêu cầu Python 3.11 trở lên.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m streamlit run app/main.py
```

Ứng dụng mặc định đọc dữ liệu mẫu từ `data/sample_transactions_onis.csv`. Chế độ local không cần AWS credentials. Để sử dụng DynamoDB hoặc agent Bedrock, cập nhật các biến tương ứng trong `.env` và cấu hình AWS credentials bằng AWS CLI, biến môi trường hoặc IAM role.

## Cấu hình

| Biến | Mục đích |
| --- | --- |
| `AWS_REGION` | Region AWS (mặc định `ap-southeast-1`) |
| `BEDROCK_MODEL_ID` | Model ID được Amazon Bedrock cung cấp |
| `DYNAMODB_TABLE_NAME` | Tên bảng DynamoDB (để trống khi chỉ dùng local) |
| `USER_ID` | Partition key người dùng cần tải (mặc định `demo`) |
| `DATA_SOURCE` | `csv` để dùng file local hoặc `dynamodb` để dùng bảng DynamoDB |
| `SAMPLE_DATA_PATH` | Đường dẫn CSV dữ liệu mẫu |

`src/config.py` đọc `.env` nếu có. Không đặt credentials thật trong `.env.example` hoặc commit file `.env`.

## Cấu trúc dự án

```text
onis-finance-agent/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── data/
│   ├── sample_transactions_onis.csv
│   └── categories_config.json
├── src/
│   ├── config.py
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── categorization.py
│   │   ├── analysis.py
│   │   └── advisory.py
│   ├── tools/
│   │   ├── calculator.py
│   │   └── lambda_handlers/calculate_balance.py
│   ├── database/
│   │   ├── dynamodb_client.py
│   │   └── local_storage.py
│   └── utils/
│       ├── data_parser.py
│       └── logger.py
├── app/
│   ├── main.py
│   ├── components/
│   │   ├── sidebar.py
│   │   ├── dashboard.py
│   │   └── chat_interface.py
│   └── assets/
└── tests/
    ├── test_agents.py
    └── test_tools.py
```

## Phát triển

```powershell
pytest
```

Agent được khởi tạo rõ ràng qua `src/agents/`; ứng dụng Streamlit không gọi Bedrock tự động. Ví dụ sử dụng `create_agent()` chỉ sau khi đã thiết lập `BEDROCK_MODEL_ID` và AWS credentials. `src/tools/calculator.py` là logic Python thuần; agent cố vấn gọi hàm này qua tool wrapper để tránh tự tính toán số liệu tài chính. Khi chọn DynamoDB, bảng cần có partition key `user_id`; ứng dụng tải giao dịch theo `USER_ID`.

## Phân công đề xuất

- **Trịnh Quyết Chiến – AI Agent & AWS Backend:** `src/agents/`, `src/tools/`; phát triển các luồng phân loại, phân tích, tư vấn và tích hợp Bedrock.
- **Hứa Huỳnh Anh – Dữ liệu, DynamoDB & UI:** `app/`, `src/database/`; phát triển giao diện Streamlit, biểu đồ và lưu trữ giao dịch.

Hai nhánh công việc dùng chung cấu trúc giao dịch và các hàm tính toán đã có trong `src/tools/calculator.py`.
