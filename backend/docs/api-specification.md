# API Specification

Base URL: `/api/v1`

## Authentication

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `POST /auth/logout`

Đặt `Authorization: Bearer <token>` khi `AUTH_REQUIRED=true`.

## AI

- `GET /health`
- `GET /api/v1/health`
- `POST /api/v1/intent/classify`
- `POST /api/v1/chat`

`chat` hỗ trợ clarification qua `slots`, HITL qua `user_confirmed` và `idempotency_key`.

## Transactions

- `GET /transactions`
- `POST /transactions`
- `GET /transactions/{transaction_id}`
- `PATCH /transactions/{transaction_id}`
- `DELETE /transactions/{transaction_id}`
- `POST /transactions/corrections`

Giao dịch lưu `amount` dưới dạng chuỗi Decimal trong repository local.

## Tasks

- `GET /tasks`
- `POST /tasks`
- `PATCH /tasks/{task_id}`
- `DELETE /tasks/{task_id}`

DELETE task không xóa trực tiếp; trả trạng thái `BLOCKED` và yêu cầu gọi HITL approval.

## Savings & Debts

- `GET/POST /savings-goals`
- `GET/POST /debts`

## HITL

- `POST /hitl/approve`

Request cần `idempotency_key`, `action` và `payload`. Approval lặp lại cùng key không thực thi lặp.
