import pytest

from src import email_service


def test_send_otp_email_uses_configured_starttls_smtp(monkeypatch):
    sent = {}

    class FakeSmtp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def starttls(self, context):
            sent["starttls"] = context

        def login(self, username, password):
            sent["login"] = (username, password)

        def send_message(self, message):
            sent["message"] = message

    monkeypatch.setenv("SMTP_HOST", "smtp.example.test")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USERNAME", "mailer")
    monkeypatch.setenv("SMTP_PASSWORD", "test-password")
    monkeypatch.setenv("SMTP_FROM", "no-reply@example.test")
    monkeypatch.setenv("SMTP_STARTTLS", "true")
    monkeypatch.setenv("SMTP_USE_SSL", "false")
    monkeypatch.setattr(email_service.smtplib, "SMTP", lambda *args, **kwargs: FakeSmtp())

    email_service.send_otp_email(
        "user@example.test",
        "012345",
        "email_verification",
    )

    message = sent["message"]
    assert message["To"] == "user@example.test"
    assert message["From"] == "no-reply@example.test"
    assert sent["login"] == ("mailer", "test-password")
    assert "012345" in message.get_content()


def test_send_otp_email_requires_smtp_configuration(monkeypatch):
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("SMTP_FROM", raising=False)
    monkeypatch.delenv("SMTP_USERNAME", raising=False)

    with pytest.raises(RuntimeError, match="SMTP_HOST"):
        email_service.send_otp_email(
            "user@example.test",
            "012345",
            "password_reset",
        )
