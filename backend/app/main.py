"""FastAPI 애플리케이션 진입점."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analysis, beltoon, health, pc
from app.config import get_settings
from app.db.database import init_db

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 개발 편의를 위해 시작 시 테이블 생성(SQLite 폴백 포함).
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="월별 POS '메뉴별 매출 순위 집계' 엑셀 2개를 업로드해 자동 비교 분석하는 AI BI 플랫폼",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(analysis.router)
    app.include_router(pc.router)
    app.include_router(beltoon.router)
    return app


app = create_app()
