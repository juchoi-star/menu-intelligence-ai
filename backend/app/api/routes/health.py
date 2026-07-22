"""헬스체크 라우트."""

from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, object]:
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "ai": "openai" if settings.openai_api_key else "rule-based",
    }
