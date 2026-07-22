"""SQLAlchemy 엔진/세션 설정."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

# SQLite 는 다중스레드 접근을 위해 check_same_thread=False 필요.
_connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(settings.database_url, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """ORM 베이스 클래스."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI 의존성: 요청 스코프 DB 세션."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """테이블 생성(개발용). 운영에서는 마이그레이션 사용 권장."""
    from app.db import models  # noqa: F401 - 모델 등록

    Base.metadata.create_all(bind=engine)
