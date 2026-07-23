"""벌툰(만화/보드게임카페) 분석 라우트.

한 달 데이터가 용량 때문에 여러 파일(날짜 범위)로 쪼개지므로,
전월·당월 각각 **여러 파일**을 받아 합산 후 비교 분석한다.
상품 단위 데이터라 PC 분석 엔진(analyze_pc)·저장소를 재사용한다.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_pc_repository
from app.config import get_settings
from app.core.beltoon_parser import BeltoonParserError, parse_beltoon_files
from app.core.pc_ai import generate_pc_ai_report
from app.core.pc_analyzer import analyze_pc
from app.db.database import get_db
from app.db.repository import PCAnalysisRepository, load_alias_map
from app.models.pc_schemas import PCAnalysisResult, PCUploadResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/beltoon", tags=["beltoon"])

_ALLOWED_EXT = (".xlsx", ".xlsm")


async def _read_all(files: list[UploadFile], side: str, max_bytes: int) -> list[bytes]:
    if not files:
        raise HTTPException(400, f"{side} 파일을 1개 이상 업로드하세요.")
    out: list[bytes] = []
    for f in files:
        if not f.filename or not f.filename.lower().endswith(_ALLOWED_EXT):
            raise HTTPException(400, f"엑셀(.xlsx) 파일만 업로드할 수 있습니다: {f.filename}")
        data = await f.read()
        if len(data) > max_bytes:
            raise HTTPException(413, f"'{f.filename}' 이(가) 너무 큽니다(최대 {max_bytes // (1024 * 1024)}MB).")
        out.append(data)
    return out


@router.post("/compare", response_model=PCUploadResponse)
async def compare(
    prev_files: list[UploadFile] = File(..., description="전월 파일들(여러 개 가능)"),
    curr_files: list[UploadFile] = File(..., description="당월 파일들(여러 개 가능)"),
    prev_label: str = Form("전월"),
    curr_label: str = Form("당월"),
    repo: PCAnalysisRepository = Depends(get_pc_repository),
    db: Session = Depends(get_db),
) -> PCUploadResponse:
    """전월·당월 각각 여러 파일을 합산해 비교 분석하고 저장/반환한다."""
    settings = get_settings()
    max_bytes = settings.max_upload_mb * 1024 * 1024

    prev_bytes = await _read_all(prev_files, "전월", max_bytes)
    curr_bytes = await _read_all(curr_files, "당월", max_bytes)

    try:
        prev = parse_beltoon_files(prev_bytes)
        curr = parse_beltoon_files(curr_bytes)
    except BeltoonParserError as exc:
        raise HTTPException(422, f"파싱 실패: {exc}") from exc

    result = analyze_pc(prev, curr, prev_label=prev_label, curr_label=curr_label,
                        alias_map=load_alias_map(db, "beltoon"))

    # 시간제·이용권 등 비메뉴 제외 안내(당월 기준)
    if curr.excluded_category_count:
        result.meta.excluded_note = (
            f"시간제·이용권 등 비메뉴 {curr.excluded_category_count}개 분류는 분석에서 제외됨 "
            f"(당월 {curr.excluded_sales:,.0f}원 · {curr.excluded_qty:,.0f}건). 메뉴·음료만 집계."
        )

    result.ai = generate_pc_ai_report(
        result, api_key=settings.openai_api_key, model=settings.openai_model
    )

    prev_names = ", ".join(f.filename or "?" for f in prev_files)
    curr_names = ", ".join(f.filename or "?" for f in curr_files)
    entity = repo.create(result, prev_filename=prev_names, curr_filename=curr_names)
    logger.info("벌툰 분석 저장 id=%s (전월 %d개 / 당월 %d개)", entity.id, len(prev_files), len(curr_files))
    return PCUploadResponse(analysis_id=entity.id, result=result)


@router.get("/{analysis_id}", response_model=PCAnalysisResult)
def get_beltoon_analysis(
    analysis_id: str,
    repo: PCAnalysisRepository = Depends(get_pc_repository),
) -> PCAnalysisResult:
    entity = repo.get(analysis_id)
    if entity is None:
        raise HTTPException(404, "분석 결과를 찾을 수 없습니다.")
    return PCAnalysisResult.model_validate(entity.result_json)
