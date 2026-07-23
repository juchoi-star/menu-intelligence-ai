"""피씨(PC방) 분석 라우트: HTML(.xls) POS 파일 2개 업로드 → 상품 비교 분석.

피씨 POS 는 매출 기간 표기가 없으므로 전월/당월은 업로드 슬롯 순서로 결정한다.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.deps import get_pc_repository
from app.config import get_settings
from app.core.pc_ai import generate_pc_ai_report
from app.core.pc_analyzer import analyze_pc
from app.core.pc_parser import PCParserError, parse_pc_html
from app.db.repository import PCAnalysisRepository
from app.models.pc_schemas import PCAnalysisResult, PCUploadResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pc", tags=["pc"])

_ALLOWED_EXT = (".xls", ".html", ".htm", ".xlsx")


async def _read_and_parse(file: UploadFile, max_bytes: int):
    if not file.filename or not file.filename.lower().endswith(_ALLOWED_EXT):
        raise HTTPException(400, f"피씨 POS 파일(.xls/.html)만 업로드할 수 있습니다: {file.filename}")
    data = await file.read()
    if len(data) > max_bytes:
        raise HTTPException(413, f"파일이 너무 큽니다(최대 {max_bytes // (1024 * 1024)}MB).")
    try:
        return parse_pc_html(data)
    except PCParserError as exc:
        raise HTTPException(422, f"'{file.filename}' 파싱 실패: {exc}") from exc


@router.post("/compare", response_model=PCUploadResponse)
async def compare(
    prev_file: UploadFile = File(..., description="전월 피씨 POS 파일"),
    curr_file: UploadFile = File(..., description="당월 피씨 POS 파일"),
    prev_label: str = Form("전월"),
    curr_label: str = Form("당월"),
    repo: PCAnalysisRepository = Depends(get_pc_repository),
) -> PCUploadResponse:
    """두 개의 월별 피씨 POS 파일을 비교 분석하고 저장/반환한다."""
    settings = get_settings()
    max_bytes = settings.max_upload_mb * 1024 * 1024

    prev = await _read_and_parse(prev_file, max_bytes)
    curr = await _read_and_parse(curr_file, max_bytes)

    result = analyze_pc(prev, curr, prev_label=prev_label, curr_label=curr_label)
    result.ai = generate_pc_ai_report(
        result, api_key=settings.openai_api_key, model=settings.openai_model
    )

    entity = repo.create(result, prev_filename=prev_file.filename, curr_filename=curr_file.filename)
    logger.info("피씨 분석 저장 id=%s", entity.id)
    return PCUploadResponse(analysis_id=entity.id, result=result)


@router.get("/{analysis_id}", response_model=PCAnalysisResult)
def get_pc_analysis(
    analysis_id: str,
    repo: PCAnalysisRepository = Depends(get_pc_repository),
) -> PCAnalysisResult:
    entity = repo.get(analysis_id)
    if entity is None:
        raise HTTPException(404, "분석 결과를 찾을 수 없습니다.")
    return PCAnalysisResult.model_validate(entity.result_json)


@router.get("")
def list_pc_analyses(
    repo: PCAnalysisRepository = Depends(get_pc_repository),
) -> list[dict[str, object]]:
    return [
        {
            "id": e.id,
            "created_at": e.created_at.isoformat(),
            "prev_label": e.prev_label,
            "curr_label": e.curr_label,
            "total_sales_curr": e.total_sales_curr,
            "sales_delta_pct": e.sales_delta_pct,
            "product_count": e.product_count,
            "ai_provider": e.ai_provider,
        }
        for e in repo.list_recent()
    ]


@router.delete("/{analysis_id}")
def delete_pc_analysis(
    analysis_id: str,
    repo: PCAnalysisRepository = Depends(get_pc_repository),
) -> dict[str, bool]:
    if not repo.delete(analysis_id):
        raise HTTPException(404, "분석 결과를 찾을 수 없습니다.")
    return {"deleted": True}
