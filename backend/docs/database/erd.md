# PostgreSQL Authentication ERD

This ERD describes only the relational Authentication tables currently present in
SQLAlchemy metadata and the Alembic migration. Finance/task JSON and DynamoDB
collections are described separately in [`../database-schema.md`](../database-schema.md).

```mermaid
erDiagram
    USERS ||--o{ AUTH_IDENTITIES : owns
    USERS ||--o{ AUTH_SESSIONS : owns
    USERS ||--o{ EMAIL_VERIFICATION_TOKENS : owns
    USERS ||--o{ PASSWORD_RESET_TOKENS : owns

    USERS {
        UUID id PK
        VARCHAR email UK
        VARCHAR display_name
        VARCHAR avatar_url "nullable"
        BOOLEAN is_active
        BOOLEAN is_verified
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    AUTH_IDENTITIES {
        UUID id PK
        UUID user_id FK
        VARCHAR provider
        VARCHAR provider_subject
        VARCHAR password_hash "nullable"
        TIMESTAMPTZ created_at
    }

    AUTH_SESSIONS {
        UUID id PK
        UUID user_id FK
        VARCHAR refresh_token_hash UK
        TIMESTAMPTZ expires_at
        TIMESTAMPTZ revoked_at "nullable"
        TIMESTAMPTZ created_at
        TIMESTAMPTZ last_used_at
    }

    EMAIL_VERIFICATION_TOKENS {
        UUID id PK
        UUID user_id FK
        VARCHAR token_hash UK
        TIMESTAMPTZ expires_at
        TIMESTAMPTZ used_at "nullable"
    }

    PASSWORD_RESET_TOKENS {
        UUID id PK
        UUID user_id FK
        VARCHAR token_hash UK
        TIMESTAMPTZ expires_at
        TIMESTAMPTZ used_at "nullable"
    }
```

Each child `user_id` is required and references `users.id` with
`ON DELETE CASCADE`. Detailed column definitions are in
[`schema.md`](schema.md); cardinality and cascade behavior are in
[`relationships.md`](relationships.md).
