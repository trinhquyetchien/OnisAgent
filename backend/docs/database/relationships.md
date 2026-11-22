# PostgreSQL Relationships

The relationships below are based on the foreign keys in
`alembic/versions/0001_authentication.py` and `src/models/auth_models.py`.

| Parent | Child | Cardinality | Ownership and delete behavior |
|---|---|---|---|
| `users` | `auth_identities` | One-to-many | Required `user_id`; FK `ON DELETE CASCADE`; ORM `delete-orphan` |
| `users` | `auth_sessions` | One-to-many | Required `user_id`; FK `ON DELETE CASCADE`; ORM `delete-orphan` |
| `users` | `email_verification_tokens` | One-to-many | Required `user_id`; FK `ON DELETE CASCADE` |
| `users` | `password_reset_tokens` | One-to-many | Required `user_id`; FK `ON DELETE CASCADE` |

Each child row belongs to exactly one user. A user can have no children or multiple
children of each type. There are no one-to-one, many-to-many, or association-table
relationships in the current relational schema.

The verification-token and reset-token models declare foreign keys but no ORM
`relationship()` property. The database referential-integrity behavior remains
defined by the foreign keys.
