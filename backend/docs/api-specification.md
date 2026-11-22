# API Specification

Base URL: `/api/v1`

## Authentication

- `POST /auth/register` (HTTP 201; sends email verification OTP)
- `POST /auth/login`
- `POST /auth/google`
- `POST /auth/refresh`
- `GET /auth/me`
- `POST /auth/logout`
- `POST /auth/logout-all`
- `POST /auth/verify-email`
- `POST /auth/resend-verification`
- `POST /auth/forgot-password`
- `POST /auth/verify-reset-token`
- `POST /auth/reset-password`
- `POST /auth/change-password`

`verify-email` và các route OTP đặt lại mật khẩu cần body `{ "email": "...", "token": "123456" }`.
OTP được gửi qua SMTP; cấu hình trong `backend/.env.example`. `logout` chấp nhận body
`{ "refresh_token": "..." }` (có thể bỏ body để thu hồi session mới nhất).
Đặt `Authorization: Bearer <token>` cho các route yêu cầu phiên đăng nhập.

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

Request cần `idempotency_key`, `action` và `payload`. Các action gồm `task_delete`,
`savings_create`, `loan_apply` và `transfer`. Approval lặp lại cùng key không thực thi lặp.
