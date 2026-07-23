"""Repository 패턴: 분석 결과 영속화 접근 계층.

비즈니스 로직은 이 인터페이스에만 의존하고, 저장소 구현(SQLAlchemy)은
언제든 교체 가능하도록 캡슐화한다.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Analysis, PCAnalysis
from app.models.pc_schemas import PCAnalysisResult
from app.models.schemas import AnalysisResult


class AnalysisRepository:
    """`analyses` 테이블에 대한 데이터 접근 객체."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        result: AnalysisResult,
        prev_filename: str | None = None,
        curr_filename: str | None = None,
    ) -> Analysis:
        """분석 결과를 저장하고 저장된 엔티티를 반환."""
        entity = Analysis(
            prev_label=result.meta.prev_label,
            curr_label=result.meta.curr_label,
            curr_period_start=result.meta.curr_period_start,
            curr_period_end=result.meta.curr_period_end,
            scope=result.meta.scope,
            store_count=result.meta.store_count,
            menu_count_curr=result.dashboard.menu_count_curr,
            total_sales_curr=result.dashboard.total_sales_curr,
            sales_delta_pct=result.dashboard.sales_delta_pct,
            ai_provider=result.ai.provider,
            result_json=result.model_dump(mode="json"),
            prev_filename=prev_filename,
            curr_filename=curr_filename,
        )
        self._db.add(entity)
        self._db.commit()
        self._db.refresh(entity)
        return entity

    def get(self, analysis_id: str) -> Analysis | None:
        return self._db.get(Analysis, analysis_id)

    def list_recent(self, limit: int = 20) -> list[Analysis]:
        stmt = select(Analysis).order_by(Analysis.created_at.desc()).limit(limit)
        return list(self._db.scalars(stmt).all())

    def delete(self, analysis_id: str) -> bool:
        entity = self.get(analysis_id)
        if entity is None:
            return False
        self._db.delete(entity)
        self._db.commit()
        return True


class PCAnalysisRepository:
    """`pc_analyses` 테이블 데이터 접근 객체."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        result: PCAnalysisResult,
        prev_filename: str | None = None,
        curr_filename: str | None = None,
    ) -> PCAnalysis:
        entity = PCAnalysis(
            prev_label=result.meta.prev_label,
            curr_label=result.meta.curr_label,
            total_sales_curr=result.dashboard.total_sales_curr,
            sales_delta_pct=result.dashboard.sales_delta_pct,
            product_count=result.meta.product_count,
            ai_provider=result.ai.provider,
            result_json=result.model_dump(mode="json"),
            prev_filename=prev_filename,
            curr_filename=curr_filename,
        )
        self._db.add(entity)
        self._db.commit()
        self._db.refresh(entity)
        return entity

    def get(self, analysis_id: str) -> PCAnalysis | None:
        return self._db.get(PCAnalysis, analysis_id)

    def list_recent(self, limit: int = 20) -> list[PCAnalysis]:
        stmt = select(PCAnalysis).order_by(PCAnalysis.created_at.desc()).limit(limit)
        return list(self._db.scalars(stmt).all())

    def delete(self, analysis_id: str) -> bool:
        entity = self.get(analysis_id)
        if entity is None:
            return False
        self._db.delete(entity)
        self._db.commit()
        return True
