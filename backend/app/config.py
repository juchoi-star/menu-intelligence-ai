"""환경변수 기반 애플리케이션 설정."""

from __future__ import annotations

import json
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """`.env` 또는 환경변수에서 로드되는 설정."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Menu Intelligence AI"
    debug: bool = False

    # 프론트엔드 오리진(CORS). 콤마 구분 문자열 또는 JSON 배열 모두 허용.
    # 예) "https://menu.vercel.app,https://staging.vercel.app"
    cors_origins: str = "http://localhost:3000"

    # PostgreSQL / Supabase / Render. 미설정 시 로컬 SQLite 로 폴백해 MVP 가 바로 돈다.
    # Render 는 postgres:// , Supabase 는 postgresql:// 스킴을 주는데
    # SQLAlchemy 는 postgresql+psycopg2:// 를 요구하므로 자동 정규화한다.
    database_url: str = "sqlite:///./menu_intelligence.db"

    # OpenAI (선택). 없으면 규칙 기반 내러티브 사용.
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    # 업로드 제한
    max_upload_mb: int = 20

    @field_validator("database_url")
    @classmethod
    def _normalize_db_url(cls, value: str) -> str:
        """클라우드 DB 스킴을 SQLAlchemy(psycopg2) 형식으로 정규화."""
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg2://", 1)
        if value.startswith("postgresql://") and "+psycopg2" not in value:
            return value.replace("postgresql://", "postgresql+psycopg2://", 1)
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        """CORS 오리진 문자열을 리스트로 파싱(콤마 구분 또는 JSON 배열)."""
        raw = self.cors_origins.strip()
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(o).strip() for o in parsed if str(o).strip()]
            except json.JSONDecodeError:
                pass
        return [o.strip() for o in raw.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """설정 싱글턴."""
    return Settings()
