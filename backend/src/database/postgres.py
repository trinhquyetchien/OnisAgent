"""SQLAlchemy database setup for authentication."""

from __future__ import annotations

import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from dotenv import load_dotenv

PROJECT_ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


class Base(DeclarativeBase):
    pass


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///data/auth.db").strip()


def create_database_engine(database_url: str | None = None) -> Engine:
    url = database_url or get_database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)


engine = create_database_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    """Initialize database tables and seed demo accounts if needed."""
    from src.models import auth_models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _seed_demo_users_if_needed()


def _seed_demo_users_if_needed() -> None:
    from sqlalchemy import select
    from src.models.auth_models import AuthUser, AuthIdentity
    from src.security import hash_password

    session = SessionLocal()
    try:
        demo_accounts = [
            {"email": "demo@onis.ai", "name": "Demo User", "verified": True},
            {"email": "alex@onis.ai", "name": "Alex Đỗ", "verified": True},
            {"email": "unverified@onis.ai", "name": "Chưa verify OTP", "verified": False},
        ]
        for acc in demo_accounts:
            existing = session.scalar(select(AuthUser).where(AuthUser.email == acc["email"]))
            if not existing:
                user = AuthUser(
                    email=acc["email"],
                    display_name=acc["name"],
                    is_verified=acc["verified"],
                    is_active=True,
                )
                session.add(user)
                session.flush()
                session.add(AuthIdentity(
                    user_id=user.id,
                    provider="local",
                    provider_subject=str(user.id),
                    password_hash=hash_password("password123"),
                ))
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"⚠️ [DB Seed Warning] Could not seed demo accounts: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    init_db()
    print("✅ Database initialized and demo accounts seeded successfully!")
