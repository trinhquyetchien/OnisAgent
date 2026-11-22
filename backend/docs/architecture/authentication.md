# Authentication Architecture

OnisAgent uses a FastAPI modular authentication layer backed by SQLAlchemy and PostgreSQL.

## Components

- API router: `src/api_auth.py`
- SQLAlchemy models: `src/models/auth_models.py`
- Security helpers: `src/security.py`
- Request schemas: `src/schemas/auth.py`
- Migrations: `alembic/versions`

## Identity model

- Local users use a `local` identity containing an Argon2id password hash.
- Google users use a `google` identity keyed by Google's `sub` claim.
- Existing email accounts are never linked automatically to a Google identity.
- Refresh tokens are stored only as SHA-256 hashes.
- Email verification and password reset tokens are also stored only as hashes.

## Token model

- Access tokens are signed JWTs with issuer, audience, issued-at and expiration claims.
- Access tokens default to 15 minutes.
- Refresh tokens contain at least 256 bits of randomness.
- Refreshing rotates the refresh token and revokes the old session.
- Reuse of a revoked refresh token revokes all sessions for that user.

## Google configuration

Set `GOOGLE_WEB_CLIENT_ID` to the Google OAuth Web Client ID. FastAPI validates the Google ID
Token signature, issuer, audience and `email_verified` claim. Flutter must pass the same Web
Client ID as `serverClientId`.

Android and iOS OAuth client configuration must be performed in the corresponding Google
platform projects; never place a Google Client Secret in Flutter.
