"""Authentication API tests with an isolated SQLite test database."""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

import src.database.postgres as postgres
from src.database.postgres import Base, create_database_engine
from src.models import auth_models  # noqa: F401


@pytest.fixture
def outbox(monkeypatch):
    emails = []

    import src.api_auth as api_auth

    monkeypatch.setattr(
        api_auth,
        "send_otp_email",
        lambda recipient, code, purpose: emails.append(
            {"recipient": recipient, "code": code, "purpose": purpose}
        ),
    )
    return emails


@pytest.fixture
def auth_client(tmp_path, monkeypatch, outbox):
    monkeypatch.setenv("AUTH_SECRET", "test-secret-with-at-least-32-bytes-of-data")
    monkeypatch.setenv("AUTH_JWT_ISSUER", "onisagent-test")
    engine = create_database_engine(f"sqlite:///{tmp_path / 'auth-test.db'}")
    Base.metadata.create_all(bind=engine)

    monkeypatch.setattr(postgres, "SessionLocal", postgres.sessionmaker(bind=engine, expire_on_commit=False))

    from src.main import app, storage
    monkeypatch.setattr(storage, "path", tmp_path / "auth-state.json")

    with TestClient(app) as client:
        yield client


def register(auth_client):
    response = auth_client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "StrongPass123!",
            "display_name": "Test User",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_register_login_and_me(auth_client, outbox):
    registered = register(auth_client)
    assert registered["user"]["email"] == "test@example.com"
    assert registered["user"]["is_verified"] is False
    assert 100 <= registered["expires_in"] <= 3600
    assert len(outbox[-1]["code"]) == 6 and outbox[-1]["code"].isdigit()

    login = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "StrongPass123!"},
    )
    assert login.status_code == 200

    me = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["user"]["id"] == registered["user"]["id"]


def test_access_token_authenticates_feature_api(auth_client):
    registered = register(auth_client)

    response = auth_client.get(
        "/api/v1/transactions",
        headers={"Authorization": f"Bearer {registered['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json() == {"transactions": []}


def test_duplicate_and_wrong_password(auth_client):
    register(auth_client)
    duplicate = auth_client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "StrongPass123!",
            "display_name": "Other",
        },
    )
    assert duplicate.status_code == 409

    wrong = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "WrongPass123!"},
    )
    assert wrong.status_code == 401


def test_refresh_rotation_and_reuse_detection(auth_client):
    registered = register(auth_client)
    old_refresh = registered["refresh_token"]

    refreshed = auth_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["refresh_token"] != old_refresh

    reused = auth_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert reused.status_code == 401


def test_logout_and_logout_all(auth_client):
    registered = register(auth_client)
    access = registered["access_token"]
    refresh = registered["refresh_token"]

    logout = auth_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access}"},
        json={"refresh_token": refresh},
    )
    assert logout.status_code == 200

    logout_all = auth_client.post(
        "/api/v1/auth/logout-all",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert logout_all.status_code == 200


def test_google_login_valid_and_invalid_token(auth_client, monkeypatch):
    monkeypatch.setenv("GOOGLE_WEB_CLIENT_ID", "test-google-audience")

    import src.api_auth as api_auth

    monkeypatch.setattr(
        api_auth.id_token,
        "verify_oauth2_token",
        lambda token, request, audience=None: {
            "iss": "accounts.google.com",
            "sub": "google-user-123",
            "email": "google@example.com",
            "email_verified": True,
            "name": "Google User",
            "picture": None,
        },
    )
    valid = auth_client.post(
        "/api/v1/auth/google",
        json={"id_token": "valid-mock-token"},
    )
    assert valid.status_code == 200
    assert valid.json()["user"]["is_verified"] is True

    def reject(*args, **kwargs):
        raise ValueError("invalid token")

    monkeypatch.setattr(api_auth.id_token, "verify_oauth2_token", reject)
    invalid = auth_client.post(
        "/api/v1/auth/google",
        json={"id_token": "invalid-mock-token"},
    )
    assert invalid.status_code == 401


def test_forgot_and_reset_password(auth_client, outbox):
    register(auth_client)

    forgot = auth_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "test@example.com"},
    )
    assert forgot.status_code == 200

    reset_code = "not-the-otp"
    reset = auth_client.post(
        "/api/v1/auth/reset-password",
        json={
            "email": "test@example.com",
            "token": reset_code,
            "new_password": "NewStrongPass123!",
        },
    )
    assert reset.status_code == 400

    # The OTP is delivered by the SMTP adapter and is not included in API responses.
    # Use the most recently issued code captured by the test outbox.
    reset_code = outbox[-1]["code"]
    reset = auth_client.post(
        "/api/v1/auth/reset-password",
        json={
            "email": "test@example.com",
            "token": reset_code,
            "new_password": "NewStrongPass123!",
        },
    )
    assert reset.status_code == 200

    login = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "NewStrongPass123!"},
    )
    assert login.status_code == 200


def test_email_verification_and_resend(auth_client, outbox):
    registered = register(auth_client)
    original_code = outbox[-1]["code"]
    assert outbox[-1]["purpose"] == "email_verification"

    resent = auth_client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "test@example.com"},
    )
    assert resent.status_code == 200
    replacement_code = outbox[-1]["code"]
    assert replacement_code != original_code

    wrong_email = auth_client.post(
        "/api/v1/auth/verify-email",
        json={"email": "other@example.com", "token": replacement_code},
    )
    assert wrong_email.status_code == 400

    expired = auth_client.post(
        "/api/v1/auth/verify-email",
        json={"email": "test@example.com", "token": original_code},
    )
    assert expired.status_code == 400

    verified = auth_client.post(
        "/api/v1/auth/verify-email",
        json={"email": "test@example.com", "token": replacement_code},
    )
    assert verified.status_code == 200
    assert verified.json()["user"]["is_verified"] is True


def test_registration_surfaces_mail_failure_and_can_resend(
    auth_client,
    monkeypatch,
):
    import src.api_auth as api_auth

    def fail_delivery(recipient, code, purpose):
        raise RuntimeError("smtp unavailable")

    monkeypatch.setattr(api_auth, "send_otp_email", fail_delivery)
    failed = auth_client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "StrongPass123!",
            "display_name": "Test User",
        },
    )
    assert failed.status_code == 503

    monkeypatch.setattr(api_auth, "send_otp_email", lambda *args: None)
    resent = auth_client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "test@example.com"},
    )
    assert resent.status_code == 200


def test_forgot_password_sends_otp_and_can_be_verified(auth_client, outbox):
    register(auth_client)
    forgot = auth_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "test@example.com"},
    )
    assert forgot.status_code == 200
    assert outbox[-1]["purpose"] == "password_reset"

    verified = auth_client.post(
        "/api/v1/auth/verify-reset-token",
        json={"email": "test@example.com", "token": outbox[-1]["code"]},
    )
    assert verified.status_code == 200

    reset = auth_client.post(
        "/api/v1/auth/reset-password",
        json={
            "email": "test@example.com",
            "token": outbox[-1]["code"],
            "new_password": "AnotherStrong123!",
        },
    )
    assert reset.status_code == 200
    assert auth_client.post(
        "/api/v1/auth/verify-reset-token",
        json={"email": "test@example.com", "token": outbox[-1]["code"]},
    ).status_code == 400


def test_logout_without_request_body(auth_client):
    registered = register(auth_client)
    response = auth_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {registered['access_token']}"},
    )
    assert response.status_code == 200
