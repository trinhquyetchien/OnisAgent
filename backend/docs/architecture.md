# Kiến trúc Backend OnisAgent

## Thành phần

- **API / Router:** FastAPI, version `/api/v1`, validation Pydantic.
- **Service:** xử lý phiên hội thoại, intent, slot và human-in-the-loop.
- **Repository:** `JsonStorage` cho phát triển/offline; DynamoDB adapter cho dữ liệu AWS.
- **AI Engine:** pipeline Kev cho Fast Path, Ollama cho Reasoning Path.
- **Tools:** Decimal calculators cho khoản vay và chia hóa đơn.

## Luồng xử lý

1. `/api/v1/intent/classify` chạy Kev inference.
2. `/api/v1/chat` tiếp nhận hội thoại, trích slot, quản lý clarification.
3. Intent đơn giản chạy Fast Path; intent phức tạp chuyển Reasoning Path.
4. Hành động tài chính nhạy cảm hoặc xóa dữ liệu phải ở trạng thái `BLOCKED` và được xác nhận qua HITL.
5. Dữ liệu persistent chỉ ghi qua repository theo `user_id`.

## Cấu trúc dữ liệu

`users`, `sessions`, `transactions`, `tasks`, `debts`, `budgets`, `savings_goals`, `reminders`, `plans`, `correction_history`, `hitl_approvals`.

Các collection trên thuộc repository JSON/DynamoDB cho miền tài chính và công
việc. PostgreSQL hiện quản lý riêng dữ liệu Authentication qua SQLAlchemy và
Alembic; xem [PostgreSQL schema](database/schema.md) và [ERD](database/erd.md).

## Quản lý cấu hình

Cấu hình môi trường nằm trong `.env`; không hardcode credential trong source.
