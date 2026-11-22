# Database Schema

This document describes the local JSON and DynamoDB repositories used by the
finance/task domain. PostgreSQL authentication tables are documented separately in
[`database/schema.md`](database/schema.md); they are managed by SQLAlchemy and
Alembic.

## Local JSON

File local mặc định: `backend/data/local/onis_state.json`.

Các collection chính:

- `users`
- `sessions`
- `transactions`
- `tasks`
- `debts`
- `budgets`
- `savings_goals`
- `reminders`
- `plans`
- `correction_history`
- `hitl_approvals`

Mọi collection nghiệp vụ có `user_id` để cô lập tenant.

## Money

Giá trị tiền được lưu dưới dạng chuỗi thập phân và chuyển sang `Decimal` tại tầng repository/calculator.

## DynamoDB

Khi `DATA_SOURCE=dynamodb`, adapter DynamoDB dùng `DYNAMODB_TABLE_NAME`. `user_id` là Partition Key theo ADR-0003. Blob và voice audio không được nhúng trực tiếp; chỉ lưu `S3 Object Key`.
