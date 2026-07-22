"""분석 라우트: 월별 POS 엑셀 2개 업로드 → 자동 비교 분석.

MVP 핵심 엔드포인트. 두 파일의 조회기간을 읽어 전월/당월을 자동 판별한다.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.api.deps import get_analysis_repository
from app.config import get_settings
from app.core.ai import generate_ai_report
from app.core.analyzer import analyze
from app.core.parser import ParsedFile, ParserError, parse_excel
from app.db.repository import AnalysisRepository
from app.models.schemas import AnalysisResult, UploadResponse
from app.services.report import build_pdf_report

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["analysis"])

_ALLOWED_EXT = (".xlsx", ".xlsm")


async def _read_and_parse(file: UploadFile, max_bytes: int) -> ParsedFile:
    if not file.filename or not file.filename.lower().endswith(_ALLOWED_EXT):
        raise HTTPException(400, f"엑셀(.xlsx) 파일만 업로드할 수 있습니다: {file.filename}")
    data = await file.read()
    if len(data) > max_bytes:
        raise HTTPException(413, f"파일이 너무 큽니다(최대 {max_bytes // (1024 * 1024)}MB).")
    try:
        return parse_excel(data)
    except ParserError as exc:
        raise HTTPException(422, f"'{file.filename}' 파싱 실패: {exc}") from exc


def _order_by_period(a: ParsedFile, b: ParsedFile) -> tuple[ParsedFile, ParsedFile]:
    """조회 시작일 기준으로 (전월, 당월) 순서로 정렬."""
    if a.period_start and b.period_start:
        return (a, b) if a.period_start <= b.period_start else (b, a)
    return a, b  # 기간 정보가 없으면 업로드 순서 유지


@router.post("/compare", response_model=UploadResponse)
async def compare(
    prev_file: UploadFile = File(..., description="전월 POS 엑셀"),
    curr_file: UploadFile = File(..., description="당월 POS 엑셀"),
    repo: AnalysisRepository = Depends(get_analysis_repository),
) -> UploadResponse:
    """두 개의 월별 POS 파일을 비교 분석하고 결과를 저장/반환한다."""
    settings = get_settings()
    max_bytes = settings.max_upload_mb * 1024 * 1024

    parsed_a = await _read_and_parse(prev_file, max_bytes)
    parsed_b = await _read_and_parse(curr_file, max_bytes)
    prev, curr = _order_by_period(parsed_a, parsed_b)

    result = analyze(prev, curr)
    result.ai = generate_ai_report(
        result, api_key=settings.openai_api_key, model=settings.openai_model
    )

    # 파일명도 정렬에 맞춰 매핑
    prev_name = prev_file.filename if prev is parsed_a else curr_file.filename
    curr_name = curr_file.filename if curr is parsed_b else prev_file.filename

    entity = repo.create(result, prev_filename=prev_name, curr_filename=curr_name)
    logger.info("분석 저장 완료 id=%s (%s -> %s)", entity.id, prev.period_label, curr.period_label)
    return UploadResponse(analysis_id=entity.id, result=result)


@router.get("/{analysis_id}", response_model=AnalysisResult)
def get_analysis(
    analysis_id: str,
    repo: AnalysisRepository = Depends(get_analysis_repository),
) -> AnalysisResult:
    """저장된 분석 결과 조회."""
    entity = repo.get(analysis_id)
    if entity is None:
        raise HTTPException(404, "분석 결과를 찾을 수 없습니다.")
    return AnalysisResult.model_validate(entity.result_json)


@router.get("")
def list_analyses(
    repo: AnalysisRepository = Depends(get_analysis_repository),
) -> list[dict[str, object]]:
    """최근 분석 목록(요약)."""
    return [
        {
            "id": e.id,
            "created_at": e.created_at.isoformat(),
            "prev_label": e.prev_label,
            "curr_label": e.curr_label,
            "total_sales_curr": e.total_sales_curr,
            "sales_delta_pct": e.sales_delta_pct,
            "store_count": e.store_count,
            "ai_provider": e.ai_provider,
        }
        for e in repo.list_recent()
    ]


@router.get("/{analysis_id}/report.pdf")
def download_report(
    analysis_id: str,
    repo: AnalysisRepository = Depends(get_analysis_repository),
) -> Response:
    """AI 보고서 PDF 다운로드."""
    entity = repo.get(analysis_id)
    if entity is None:
        raise HTTPException(404, "분석 결과를 찾을 수 없습니다.")
    result = AnalysisResult.model_validate(entity.result_json)
    pdf_bytes = build_pdf_report(result)
    filename = f"menu_report_{result.meta.curr_label}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{analysis_id}")
def delete_analysis(
    analysis_id: str,
    repo: AnalysisRepository = Depends(get_analysis_repository),
) -> dict[str, bool]:
    if not repo.delete(analysis_id):
        raise HTTPException(404, "분석 결과를 찾을 수 없습니다.")
    return {"deleted": True}
