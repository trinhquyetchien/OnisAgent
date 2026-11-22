"""SMTP delivery for authentication one-time passwords."""

from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage


def send_otp_email(recipient: str, code: str, purpose: str) -> None:
    host = os.getenv("SMTP_HOST", "").strip()
    username = os.getenv("SMTP_USERNAME", "").strip()
    password = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("SMTP_FROM", "").strip() or username
    port = int(os.getenv("SMTP_PORT", "587"))
    use_ssl = os.getenv("SMTP_USE_SSL", "false").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    starttls_setting = os.getenv("SMTP_STARTTLS")
    use_starttls = (
        not use_ssl
        if starttls_setting is None
        else starttls_setting.strip().lower() in {"1", "true", "yes"}
    )

    if not host or not sender:
        raise RuntimeError("SMTP_HOST and SMTP_FROM (or SMTP_USERNAME) are required.")
    if use_ssl and use_starttls:
        raise RuntimeError("Configure SMTP_USE_SSL or SMTP_STARTTLS, not both.")
    if bool(username) != bool(password):
        raise RuntimeError("SMTP_USERNAME and SMTP_PASSWORD must be configured together.")

    if purpose == "email_verification":
        subject = "Xác thực email OnisAgent"
        action = "xác thực địa chỉ email"
        expiry = "10 phút"
    elif purpose == "password_reset":
        subject = "Đặt lại mật khẩu OnisAgent"
        action = "đặt lại mật khẩu"
        expiry = "30 phút"
    else:
        raise ValueError(f"Unsupported OTP purpose: {purpose}")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        f"Mã OTP để {action} của bạn là: {code}\n\n"
        f"Mã có hiệu lực trong {expiry}. Nếu bạn không yêu cầu thao tác này, "
        "hãy bỏ qua email."
    )

    timeout = float(os.getenv("SMTP_TIMEOUT_SECONDS", "10"))
    context = ssl.create_default_context()
    if use_ssl:
        with smtplib.SMTP_SSL(host, port, timeout=timeout, context=context) as server:
            if username:
                server.login(username, password)
            server.send_message(message)
        return

    with smtplib.SMTP(host, port, timeout=timeout) as server:
        if use_starttls:
            server.starttls(context=context)
        if username:
            server.login(username, password)
        server.send_message(message)
