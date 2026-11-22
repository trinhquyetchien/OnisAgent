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
- Email verification and password reset codes are six-digit OTPs; verification codes expire
  after 10 minutes and reset codes after 30 minutes. The API requires the matching email.
- OTP delivery uses SMTP. Configure `SMTP_HOST`, `SMTP_FROM`, `SMTP_PORT`, and either
  `SMTP_STARTTLS=true` (default, typically port 587) or `SMTP_USE_SSL=true` (typically port 465).
  Configure `SMTP_USERNAME` and `SMTP_PASSWORD` together when the server requires authentication.
  Keep the SMTP password in the untracked `backend/.env`, not in source control.
- `POST /api/v1/auth/resend-verification` issues and emails a replacement verification code.
- If mail delivery fails, the API reports HTTP 503; registration may already have created the
  account, in which case resend the verification code instead of registering again.

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
