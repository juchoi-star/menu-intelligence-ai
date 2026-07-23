"""ORM 모델.

분석 결과 원본(JSON)과 요약 메타를 저장한다. 상세 결과는 재현이 쉬우므로
정규화하지 않고 JSON 컬럼에 통째로 보관(조회/재표시 용도)한다.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import JSON, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


class Analysis(Base):
    """한 번의 비교 분석(전월 vs 당월) 저장 레코드."""

    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    prev_label: Mapped[str] = mapped_column(String(16))
    curr_label: Mapped[str] = mapped_column(String(16))
    curr_period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    curr_period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    scope: Mapped[str | None] = mapped_column(String(64), nullable=True)

    store_count: Mapped[int] = mapped_column(Integer, default=0)
    menu_count_curr: Mapped[int] = mapped_column(Integer, default=0)
    total_sales_curr: Mapped[float] = mapped_column(Float, default=0.0)
    sales_delta_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_provider: Mapped[str] = mapped_column(String(32), default="rule-based")

    # 전체 AnalysisResult 직렬화 결과
    result_json: Mapped[dict] = mapped_column(JSON)

    # 원본 파일명(감사/추적용)
    prev_filename: Mapped[str | None] = mapped_column(Text, nullable=True)
    curr_filename: Mapped[str | None] = mapped_column(Text, nullable=True)


class PCAnalysis(Base):
    """피씨(PC방) 비교 분석 저장 레코드(생전포차와 스키마가 달라 별도 테이블)."""

    __tablename__ = "pc_analyses"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    prev_label: Mapped[str] = mapped_column(String(32))
    curr_label: Mapped[str] = mapped_column(String(32))
    total_sales_curr: Mapped[float] = mapped_column(Float, default=0.0)
    sales_delta_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    product_count: Mapped[int] = mapped_column(Integer, default=0)
    ai_provider: Mapped[str] = mapped_column(String(32), default="rule-based")

    result_json: Mapped[dict] = mapped_column(JSON)

    prev_filename: Mapped[str | None] = mapped_column(Text, nullable=True)
    curr_filename: Mapped[str | None] = mapped_column(Text, nullable=True)


class AliasSet(Base):
    """브랜드별 수동 별칭표(유사/동의어 메뉴 병합 규칙). 팀 공유(단일 레코드/브랜드)."""

    __tablename__ = "alias_sets"

    brand: Mapped[str] = mapped_column(String(32), primary_key=True)  # sjp | pc | beltoon
    # [{"canonical": "아이스 아메리카노", "members": ["아이스아메리카노","아메리카노(ice)"]}]
    groups: Mapped[list] = mapped_column(JSON, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
