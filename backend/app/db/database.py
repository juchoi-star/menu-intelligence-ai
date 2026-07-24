"""SQLAlchemy 엔진/세션 설정."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

_is_sqlite = settings.database_url.startswith("sqlite")

# SQLite 는 다중스레드 접근을 위해 check_same_thread=False 필요.
# PostgreSQL(Supabase 풀러)은 유휴 후 죽은 연결(stale)로 첫 요청이 무한 대기하는 문제가 있어
# connect_timeout 을 짧게 두고 keepalive 를 켠다.
if _is_sqlite:
    _connect_args: dict = {"check_same_thread": False}
else:
    _connect_args = {
        "connect_timeout": 10,          # 연결 자체가 지연되면 빨리 실패(무한 대기 방지)
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 3,
    }

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    future=True,
    pool_pre_ping=True,   # 사용 전 연결 생존 확인(죽은 연결이면 재연결) — stale 커넥션 hang 방지
    pool_recycle=1800,    # 30분 지난 연결은 폐기
)
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
