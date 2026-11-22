# PostgreSQL Constraints and Indexes

This inventory reflects `src/models/auth_models.py` and
`alembic/versions/0001_authentication.py`.

## Primary keys and foreign keys

- Every table has a UUID primary key.
- `auth_identities.user_id`, `auth_sessions.user_id`,
  `email_verification_tokens.user_id`, and `password_reset_tokens.user_id` are
  non-null foreign keys to `users.id` with `ON DELETE CASCADE`.

## Unique constraints and indexes

| Table | Rule | Definition |
|---|---|---|
| `users` | Unique email | Unique index `ix_users_email` |
| `auth_identities` | Provider identity unique | Constraint `uq_auth_identity_provider_subject` on `(provider, provider_subject)` |
| `auth_identities` | User/provider lookup | Index `ix_auth_identity_user_provider` on `(user_id, provider)` |
| `auth_sessions` | Refresh hash unique | Unique constraint on `refresh_token_hash` |
| `email_verification_tokens` | Verification hash unique | Unique constraint on `token_hash` |
| `password_reset_tokens` | Reset hash unique | Unique constraint on `token_hash` |

## Nullability and defaults

- Foreign-key columns, primary keys, and unique token/hash columns are non-null.
- `avatar_url`, `password_hash`, `revoked_at`, and token `used_at` are nullable.
- UUID and boolean defaults on `users` and UUID defaults on other models are
  SQLAlchemy client-side defaults, not PostgreSQL server defaults.
- Timestamp creation defaults use PostgreSQL `now()`. `users.updated_at` also has
  a SQLAlchemy `onupdate=now()` expression; there is no database trigger.
- No check constraints are currently defined.

For column-by-column details, see [`schema.md`](schema.md).
