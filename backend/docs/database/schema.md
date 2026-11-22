# PostgreSQL Authentication Schema

This is the canonical relational schema reference for tables currently mapped by
SQLAlchemy and managed by Alembic. The finance/task domain collections described in
[`../database-schema.md`](../database-schema.md) are stored by the JSON/DynamoDB
repositories; they are not PostgreSQL tables in the current Alembic metadata.

The schema is defined in `src/models/auth_models.py` and revision
`alembic/versions/0001_authentication.py`. PostgreSQL is the intended relational
database; SQLite is used by isolated tests.

## Tables and columns

Types below are PostgreSQL equivalents. “Client default” is applied by SQLAlchemy,
not by a database server default.

### `users`

| Column | Type | Nullable | Key / default |
|---|---|---:|---|
| `id` | UUID | No | Primary key; client default `uuid4()` |
| `email` | VARCHAR(254) | No | Unique index `ix_users_email` |
| `display_name` | VARCHAR(100) | No | — |
| `avatar_url` | VARCHAR(2048) | Yes | — |
| `is_active` | BOOLEAN | No | Client default `True` |
| `is_verified` | BOOLEAN | No | Client default `False` |
| `created_at` | TIMESTAMP WITH TIME ZONE | No | Server default `now()` |
| `updated_at` | TIMESTAMP WITH TIME ZONE | No | Server default `now()`; SQLAlchemy updates it on ORM updates |

### `auth_identities`

| Column | Type | Nullable | Key / default |
|---|---|---:|---|
| `id` | UUID | No | Primary key; client default `uuid4()` |
| `user_id` | UUID | No | FK to `users.id`, `ON DELETE CASCADE` |
| `provider` | VARCHAR(32) | No | — |
| `provider_subject` | VARCHAR(255) | No | — |
| `password_hash` | VARCHAR(255) | Yes | — |
| `created_at` | TIMESTAMP WITH TIME ZONE | No | Server default `now()` |

Unique constraint: `(provider, provider_subject)`.

### `auth_sessions`

| Column | Type | Nullable | Key / default |
|---|---|---:|---|
| `id` | UUID | No | Primary key; client default `uuid4()` |
| `user_id` | UUID | No | FK to `users.id`, `ON DELETE CASCADE` |
| `refresh_token_hash` | VARCHAR(64) | No | Unique |
| `expires_at` | TIMESTAMP WITH TIME ZONE | No | — |
| `revoked_at` | TIMESTAMP WITH TIME ZONE | Yes | — |
| `created_at` | TIMESTAMP WITH TIME ZONE | No | Server default `now()` |
| `last_used_at` | TIMESTAMP WITH TIME ZONE | No | Server default `now()` |

### `email_verification_tokens`

| Column | Type | Nullable | Key / default |
|---|---|---:|---|
| `id` | UUID | No | Primary key; client default `uuid4()` |
| `user_id` | UUID | No | FK to `users.id`, `ON DELETE CASCADE` |
| `token_hash` | VARCHAR(64) | No | Unique |
| `expires_at` | TIMESTAMP WITH TIME ZONE | No | — |
| `used_at` | TIMESTAMP WITH TIME ZONE | Yes | — |

### `password_reset_tokens`

| Column | Type | Nullable | Key / default |
|---|---|---:|---|
| `id` | UUID | No | Primary key; client default `uuid4()` |
| `user_id` | UUID | No | FK to `users.id`, `ON DELETE CASCADE` |
| `token_hash` | VARCHAR(64) | No | Unique |
| `expires_at` | TIMESTAMP WITH TIME ZONE | No | — |
| `used_at` | TIMESTAMP WITH TIME ZONE | Yes | — |

## Relationships and integrity

- One `users` row may own zero or more identities, sessions, email-verification
  tokens, and password-reset tokens.
- Every child row requires a `user_id`. Deleting a user cascades to its child rows
  at the database level.
- The ORM also configures `delete-orphan` for a user's identities and sessions.
- No many-to-many or check constraints are currently defined.

See the [ERD](erd.md), [relationships](relationships.md), and
[constraints and indexes](constraints-and-indexes.md) for focused references.

## Migration status

The migration history is recorded in [migration-history.md](migration-history.md).
The migration file defines the schema; this document does not claim that a
particular running database has been migrated. Follow the
[migration guide](../development/database-migration-guide.md) to review and test
changes on an isolated PostgreSQL database.
