"""Pydantic schemas for authentication APIs."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)
    display_name: str = Field(min_length=1, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class GoogleLoginRequest(BaseModel):
    id_token: str = Field(min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=1)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=256)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=8, max_length=256)


class AuthUserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    avatar_url: str | None = None
    is_verified: bool


class TokenResponse(BaseModel):
    user: AuthUserResponse
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
