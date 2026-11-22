# Authentication API

Base path: `/api/v1/auth`

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/register` | Register local account |
| POST | `/login` | Email/password login |
| POST | `/google` | Verify Google ID Token |
| POST | `/refresh` | Rotate refresh token |
| POST | `/logout` | Revoke current refresh session |
| POST | `/logout-all` | Revoke all user sessions |
| GET | `/me` | Get current user |
| POST | `/verify-email` | Verify email token |
| POST | `/forgot-password` | Request password reset |
| POST | `/reset-password` | Reset password |
| POST | `/change-password` | Change password |

## Example login

```json
{
  "email": "user@example.com",
  "password": "StrongPass123!"
}
```

Response:

```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "display_name": "User",
    "is_verified": false
  },
  "access_token": "jwt",
  "refresh_token": "opaque-random-token",
  "token_type": "Bearer"
}
```

The refresh token must be stored by the client in secure storage. Access tokens are kept in memory.
