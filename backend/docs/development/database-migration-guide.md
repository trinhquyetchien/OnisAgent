# Database Migration Guide

## Scope and source of truth

PostgreSQL Authentication schema changes are defined by SQLAlchemy models in
`src/models/auth_models.py` and Alembic revisions in `alembic/versions/`. Alembic
is the only supported mechanism for changing that schema. Application startup must
not create or recreate tables with `Base.metadata.create_all()`.

The finance/task collections in `JsonStorage` and DynamoDB are a separate
persistence path; do not describe them as PostgreSQL tables unless their storage
implementation changes.

## Required workflow for a schema change

1. Determine affected tables, columns, relationships, constraints, indexes, data,
   and API contracts before editing.
2. Update SQLAlchemy models first. Do not generate a migration for a documentation-
   only or non-schema change.
3. Start or select an isolated PostgreSQL test database. For a disposable local
   instance, run this in a separate terminal; it does not use a persistent volume:

   ```powershell
   docker run --name onisagent-pg-test --rm `
     -e POSTGRES_DB=onisagent_test `
     -e POSTGRES_USER=postgres `
     -e POSTGRES_PASSWORD=test-only-password `
     -p 127.0.0.1:55432:5432 postgres:16-alpine
   ```

     Stop this disposable test server with Ctrl+C after verification; its test data is
     intentionally not persisted.
4. Point Alembic at the test database, apply the existing baseline, then generate
     the new revision:

   ```powershell
   cd backend
   $env:DATABASE_URL = "postgresql+psycopg://postgres:test-only-password@localhost:55432/onisagent_test"
   alembic upgrade head
   alembic current
   alembic revision --autogenerate -m "descriptive_change"
   ```

5. Review both `upgrade()` and `downgrade()` operations. Confirm names, types,
   nullability, defaults, foreign keys, delete behavior, indexes, unique/check
   constraints, dependencies, and data migration safety. Autogenerate is a draft,
   not an approval.
6. Test the revision against the isolated PostgreSQL test database, never the
   development or production database:

   ```powershell
   $env:DATABASE_URL = "postgresql+psycopg://postgres:test-only-password@localhost:55432/onisagent_test"
   alembic upgrade head
   alembic current
   alembic heads
   alembic check
   ```

   Verify tables, columns, constraints, indexes, and relationships on PostgreSQL.
   Record representative row counts or fixtures before and after if the migration
   changes data. Test downgrade and re-upgrade only on a disposable test database
   and only when rollback is safe:

   ```powershell
   alembic downgrade -1
   alembic upgrade head
   ```

   The command above requires a PostgreSQL test server listening on port `55432`
   and a dedicated `onisagent_test` database. It must not be pointed at the
   development database.
7. Synchronize [`../database/schema.md`](../database/schema.md), the
   [ERD](../database/erd.md), [relationships](../database/relationships.md),
   [constraints and indexes](../database/constraints-and-indexes.md), and
   [migration history](../database/migration-history.md). Update API docs only if
   the API contract or behavior changes.
8. Apply a reviewed, tested migration to development only as an explicit step:

   ```powershell
   alembic upgrade head
   ```

   In Docker Compose, run it explicitly with
   `docker compose run --rm backend alembic upgrade head`. Migrations are not run
   automatically on backend startup.

## Checks and safety

- `alembic current`, `alembic heads`, and `alembic check` must be run against the
  intended database context. `alembic check` requires a live connection.
- Run backend and authentication tests using their isolated test databases. The
  current `tests/test_postgres_auth.py` fixture creates SQLite; it is not evidence
  that a migration works on PostgreSQL.
- Never reset Alembic history or apply destructive downgrades to a database with
  valuable data. Assess impact, backup/rollback strategy, and request confirmation
  before any potentially data-losing operation.
- Report implemented, migrated, tested, and documented states separately. Do not
  claim a live migration or schema verification that was not actually performed.
