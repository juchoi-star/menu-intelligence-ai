"""API 공용 의존성."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.repository import AnalysisRepository


def get_analysis_repository(db: Session = Depends(get_db)) -> AnalysisRepository:
    """요청 스코프 Repository 주입."""
    return AnalysisRepository(db)
