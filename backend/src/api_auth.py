"""Secure authentication API routes backed by PostgreSQL/SQLAlchemy."""

from __future__ import annotations

import os
import logging
import smtplib
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from src.database.postgres import get_db
from src.email_service import send_otp_email
from src.models.auth_models import (
    AuthIdentity,
    AuthSession,
    AuthUser,
    EmailVerificationToken,
    PasswordResetToken,
)
from src.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    GoogleLoginRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from src.security import (
    generate_token,
    generate_otp,
    hash_password,
    hash_token,
    issue_access_token,
    verify_access_token,
    verify_password,
)


router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])
logger = logging.getLogger(__name__)


def _secret() -> str:
    secret = os.getenv("AUTH_SECRET", "").strip()
    if not secret or secret == "replace-with-a-long-random-secret":
        # In development/local mode, fallback to a default dev secret so it works out-of-the-box
        if os.getenv("APP_ENV", "development").lower() != "production":
            return "onisagent-local-development-secret-key-32-chars-long"
        raise HTTPException(status_code=500, detail="Authentication secret is not configured.")
    return secret


def _issuer() -> str:
    return os.getenv("AUTH_JWT_ISSUER", "onisagent").strip()


def _access_minutes() -> int:
    return int(os.getenv("AUTH_ACCESS_TOKEN_MINUTES", "15"))


def _refresh_days() -> int:
    return int(os.getenv("AUTH_REFRESH_TOKEN_DAYS", "30"))


def _token_response(user: AuthUser, access: str, refresh: str) -> dict:
    return {
        "user": _public_user(user),
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "Bearer",
        "expires_in": _access_minutes() * 60,
    }


def _send_otp(recipient: str, code: str, purpose: str) -> None:
    try:
        send_otp_email(recipient, code, purpose)
    except (OSError, RuntimeError, ValueError, smtplib.SMTPException):
        logger.exception("Could not deliver %s OTP email", purpose)
        detail = (
            "Không gửi được email xác thực; tài khoản có thể đã được tạo. "
            "Hãy kiểm tra SMTP, đăng nhập rồi gửi lại mã."
            if purpose == "email_verification"
            else "Không thể gửi email lúc này. Vui lòng kiểm tra cấu hình SMTP hoặc thử lại sau."
        )
        raise HTTPException(
            status_code=503,
            detail=detail,
        ) from None


def _otp_hash(user_id: object, code: str) -> str:
    return hash_token(f"{user_id}:{code}")


def _create_email_verification_code(db: Session, user: AuthUser) -> str:
    now = datetime.now(timezone.utc)
    previous = db.scalars(
        select(EmailVerificationToken).where(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.used_at.is_(None),
        )
    )
    for token in previous:
        token.used_at = now
    code = generate_otp()
    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=_otp_hash(user.id, code),
            expires_at=now + timedelta(minutes=10),
        )
    )
    db.commit()
    return code


def _utc(value: datetime) -> datetime:
    """Normalize SQLite/Python values to timezone-aware UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _public_user(user: AuthUser) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "full_name": user.display_name,
        "name": user.display_name,
        "avatar_url": user.avatar_url,
        "is_verified": user.is_verified,
        "is_email_verified": user.is_verified,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def _issue_token_pair(db: Session, user: AuthUser) -> tuple[str, str]:
    access = issue_access_token(user.id, _secret(), _issuer(), _access_minutes())
    refresh = generate_token()
    expires = datetime.now(timezone.utc) + timedelta(days=_refresh_days())
    db.add(AuthSession(
        user_id=user.id,
        refresh_token_hash=hash_token(refresh),
        expires_at=expires,
        last_used_at=datetime.now(timezone.utc),
    ))
    db.commit()
    return access, refresh


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> AuthUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Cần đăng nhập.")
    token = authorization.split(" ", 1)[1].strip()
    try:
        user_id = verify_access_token(token, _secret(), _issuer())
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc đã hết hạn.")
    user = db.scalar(select(AuthUser).where(AuthUser.id == user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Tài khoản không khả dụng.")
    return user


@router.post("/register", status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    email = str(request.email).strip().lower()
    existing = db.scalar(select(AuthUser).where(AuthUser.email == email))
    if existing:
        raise HTTPException(status_code=409, detail="Email đã được đăng ký.")

    user = AuthUser(
        email=email,
        display_name=request.display_name.strip(),
        is_verified=False,
        is_active=True,
    )
    db.add(user)
    db.flush()
    db.add(AuthIdentity(
        user_id=user.id,
        provider="local",
        provider_subject=str(user.id),
        password_hash=hash_password(request.password),
    ))
    db.commit()
    code = _create_email_verification_code(db, user)
    access, refresh = _issue_token_pair(db, user)
    _send_otp(email, code, "email_verification")
    return _token_response(user, access, refresh)


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    email = str(request.email).strip().lower()
    user = db.scalar(select(AuthUser).where(AuthUser.email == email))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng.")
    identity = db.scalar(select(AuthIdentity).where(
        AuthIdentity.user_id == user.id,
        AuthIdentity.provider == "local",
    ))
    if not identity or not identity.password_hash or not verify_password(identity.password_hash, request.password):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng.")
    if not user.is_verified:
        code = _create_email_verification_code(db, user)
        _send_otp(email, code, "email_verification")
    access, refresh = _issue_token_pair(db, user)
    return _token_response(user, access, refresh)


@router.post("/google")
def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    audience = os.getenv("GOOGLE_WEB_CLIENT_ID", "").strip()
    if not audience:
        raise HTTPException(status_code=503, detail="Google Sign-In chưa được cấu hình.")
    try:
        claims = id_token.verify_oauth2_token(
            request.id_token,
            google_requests.Request(),
            audience=audience,
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Google ID Token không hợp lệ.") from exc
    if claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise HTTPException(status_code=401, detail="Google issuer không hợp lệ.")
    if not claims.get("email_verified"):
        raise HTTPException(status_code=401, detail="Email Google chưa được xác thực.")
    subject = str(claims.get("sub", "")).strip()
    email = str(claims.get("email", "")).strip().lower()
    if not subject or not email:
        raise HTTPException(status_code=401, detail="Google token thiếu thông tin bắt buộc.")

    identity = db.scalar(select(AuthIdentity).where(
        AuthIdentity.provider == "google",
        AuthIdentity.provider_subject == subject,
    ))
    if identity:
        user = db.get(AuthUser, identity.user_id)
    else:
        # Never auto-link solely by email. Create a separate local account for a new Google identity.
        user = db.scalar(select(AuthUser).where(AuthUser.email == email))
        if user:
            raise HTTPException(
                status_code=409,
                detail="Email đã tồn tại. Cần liên kết tài khoản Google bằng luồng xác thực có chủ đích.",
            )
        user = AuthUser(
            email=email,
            display_name=str(claims.get("name") or email.split("@")[0]).strip()[:100],
            avatar_url=claims.get("picture"),
            is_verified=True,
            is_active=True,
        )
        db.add(user)
        db.flush()
        db.add(AuthIdentity(
            user_id=user.id,
            provider="google",
            provider_subject=subject,
        ))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Tài khoản không khả dụng.")
    db.commit()
    access, refresh = _issue_token_pair(db, user)
    return _token_response(user, access, refresh)


@router.post("/refresh")
def refresh(request: RefreshRequest, db: Session = Depends(get_db)):
    digest = hash_token(request.refresh_token)
    session = db.scalar(select(AuthSession).where(AuthSession.refresh_token_hash == digest))
    now = datetime.now(timezone.utc)
    if not session:
        raise HTTPException(status_code=401, detail="Refresh token không hợp lệ.")
    if session.revoked_at or _utc(session.expires_at) <= now:
        user_sessions = db.scalars(select(AuthSession).where(AuthSession.user_id == session.user_id))
        for item in user_sessions:
            if not item.revoked_at:
                item.revoked_at = now
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh token không hợp lệ hoặc đã được sử dụng.")

    user = db.get(AuthUser, session.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Tài khoản không khả dụng.")
    session.revoked_at = now
    access, refresh_token = _issue_token_pair(db, user)
    return _token_response(user, access, refresh_token)


@router.post("/logout")
def logout(
    request: LogoutRequest | None = None,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = None
    if request and request.refresh_token:
        session = db.scalar(select(AuthSession).where(
            AuthSession.user_id == user.id,
            AuthSession.refresh_token_hash == hash_token(request.refresh_token),
        ))
    else:
        latest = db.scalar(
            select(AuthSession)
            .where(AuthSession.user_id == user.id)
            .order_by(AuthSession.created_at.desc())
        )
        session = latest
    if session and not session.revoked_at:
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()
    return {"ok": True}


@router.post("/logout-all")
def logout_all(user: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    sessions = db.scalars(select(AuthSession).where(AuthSession.user_id == user.id))
    for item in sessions:
        if not item.revoked_at:
            item.revoked_at = now
    db.commit()
    return {"ok": True}


@router.get("/me")
def me(user: AuthUser = Depends(get_current_user)):
    return {"user": _public_user(user)}


@router.post("/verify-email")
def verify_email(
    request: VerifyEmailRequest,
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    email = str(request.email).strip().lower()
    user = db.scalar(select(AuthUser).where(AuthUser.email == email))
    if not user:
        raise HTTPException(status_code=400, detail="Token xác thực email không hợp lệ hoặc đã hết hạn.")
    digest = _otp_hash(user.id, request.token)
    record = db.scalar(select(EmailVerificationToken).where(
        EmailVerificationToken.user_id == user.id,
        EmailVerificationToken.token_hash == digest,
    ))
    if not record or record.used_at or _utc(record.expires_at) <= now:
        raise HTTPException(status_code=400, detail="Token xác thực email không hợp lệ hoặc đã hết hạn.")
    record.used_at = now
    user.is_verified = True
    db.commit()
    return {"ok": True, "user": _public_user(user)}


@router.post("/resend-verification")
def resend_verification(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    email = str(request.email).strip().lower()
    user = db.scalar(select(AuthUser).where(AuthUser.email == email))
    if user and user.is_active and not user.is_verified:
        code = _create_email_verification_code(db, user)
        _send_otp(email, code, "email_verification")
    return {"ok": True, "message": "Nếu tài khoản cần xác thực, mã mới đã được gửi."}


@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    email = str(request.email).strip().lower()
    user = db.scalar(select(AuthUser).where(AuthUser.email == email))
    if user:
        now = datetime.now(timezone.utc)
        previous = db.scalars(
            select(PasswordResetToken).where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used_at.is_(None),
            )
        )
        for token in previous:
            token.used_at = now
        code = generate_otp()
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=_otp_hash(user.id, code),
                expires_at=now + timedelta(minutes=30),
            )
        )
        db.commit()
        _send_otp(email, code, "password_reset")
    # Deliberately identical whether the email exists to reduce account enumeration.
    return {"ok": True, "message": "Nếu email tồn tại, hướng dẫn đặt lại mật khẩu đã được gửi."}


@router.post("/verify-reset-token")
def verify_reset_token(request: VerifyEmailRequest, db: Session = Depends(get_db)):
    email = str(request.email).strip().lower()
    user = db.scalar(select(AuthUser).where(AuthUser.email == email))
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Token đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.",
        )
    record = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.token_hash == _otp_hash(user.id, request.token),
        )
    )
    if (
        not record
        or record.used_at
        or _utc(record.expires_at) <= datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=400,
            detail="Token đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.",
        )
    return {"ok": True}


@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    email = str(request.email).strip().lower()
    user = db.scalar(select(AuthUser).where(AuthUser.email == email))
    if not user:
        raise HTTPException(status_code=400, detail="Token đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.")
    record = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.token_hash == _otp_hash(user.id, request.token),
        )
    )
    now = datetime.now(timezone.utc)
    if not record or record.used_at or _utc(record.expires_at) <= now:
        raise HTTPException(status_code=400, detail="Token đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.")
    identity = db.scalar(select(AuthIdentity).where(
        AuthIdentity.user_id == user.id,
        AuthIdentity.provider == "local",
    ))
    if not identity:
        raise HTTPException(status_code=400, detail="Tài khoản không hỗ trợ mật khẩu cục bộ.")
    identity.password_hash = hash_password(request.new_password)
    record.used_at = now
    sessions = db.scalars(select(AuthSession).where(AuthSession.user_id == user.id))
    for session in sessions:
        if not session.revoked_at:
            session.revoked_at = now
    db.commit()
    return {"ok": True}


@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    identity = db.scalar(select(AuthIdentity).where(
        AuthIdentity.user_id == user.id,
        AuthIdentity.provider == "local",
    ))
    if not identity or not identity.password_hash or not verify_password(identity.password_hash, request.old_password):
        raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không đúng.")
    identity.password_hash = hash_password(request.new_password)
    now = datetime.now(timezone.utc)
    sessions = db.scalars(select(AuthSession).where(AuthSession.user_id == user.id))
    for session in sessions:
        if not session.revoked_at:
            session.revoked_at = now
    db.commit()
    return {"ok": True}
