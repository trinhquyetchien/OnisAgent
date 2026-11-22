# Alembic Migration History

This is a summary of the checked-in Alembic revisions, not a substitute for the
revision files or proof that a database has applied them.

| Revision | File / name | Created | Purpose and affected schema | Rollback | Verification status |
|---|---|---|---|---|---|
| `0001_authentication` | `0001_authentication.py` / Create authentication tables | 2026-11-22 | Creates `users`, `auth_identities`, `auth_sessions`, `email_verification_tokens`, and `password_reset_tokens`, with their foreign keys, unique rules, and indexes | `downgrade()` drops all five tables and their data; destructive on a populated database | Offline SQL rendering succeeded. PostgreSQL upgrade/downgrade and live schema verification are pending. |

`alembic heads` reports `0001_authentication` as the current script head. The
revision's application state in any PostgreSQL database has not been verified in
this environment. Use the [migration guide](../development/database-migration-guide.md)
to test revisions against an isolated PostgreSQL database before applying them to
development or shared environments.
