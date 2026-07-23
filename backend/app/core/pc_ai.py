"""피씨(PC방) AI 분석 내러티브 (OpenAI + 규칙기반 폴백).

PC 데이터는 할인·이익이 없으므로 매출·판매개수·객단가·순위 변화 중심으로 스토리를 만든다.
"""

from __future__ import annotations

import json
import logging

from app.models.pc_schemas import PCAnalysisResult, PCProductAnalysis, PCAIReport

logger = logging.getLogger(__name__)
_NARRATIVE_LIMIT = 12


def _won(v: float) -> str:
    return f"{v:,.0f}원"


def _narrative_for(p: PCProductAnalysis) -> str:
    if p.is_new:
        return (f"{p.name}은(는) 이번 달 신규 진입해 매출 {_won(p.curr.sales)}"
                f"({p.curr.qty:,.0f}개)을 기록했습니다. 초기 반응을 지켜볼 필요가 있습니다.")
    if p.is_discontinued:
        return (f"{p.name}은(는) 전월 {_won(p.prev.sales if p.prev else 0)} 매출이 있었으나 "
                f"이번 달 판매가 없습니다. 품절·단종 여부 확인이 필요합니다.")
    sg, qg = p.sales_growth_pct, p.qty_growth_pct
    if sg is not None and sg <= -25:
        return (f"{p.name}은(는) 판매개수가 {qg}%, 매출이 {sg}% 감소했습니다. "
                f"진열/추천 위치나 재고를 점검하세요.")
    if sg is not None and sg >= 25:
        price_note = ""
        if p.price_change_pct and p.price_change_pct > 1:
            price_note = f" 객단가도 {p.price_change_pct}% 올랐는데 판매가 늘어 수요가 견조합니다."
        elif qg is not None:
            price_note = f" 판매개수가 {qg}% 늘어 실수요 증가로 보입니다."
        return f"{p.name}은(는) 매출이 {sg}% 증가했습니다.{price_note}"
    return f"{p.name}의 매출은 전월 대비 {sg}% 변동, 당월 점유율 {p.contribution_pct}% 입니다."


def _select(result: PCAnalysisResult) -> list[PCProductAnalysis]:
    names: list[str] = []
    for grp in (result.insights.rising_top10, result.insights.falling_top10,
                result.insights.new_products[:3], result.insights.discontinued_products[:3]):
        for it in grp:
            if it.name not in names:
                names.append(it.name)
    by_name = {p.name: p for p in result.products}
    return [by_name[n] for n in names if n in by_name][:_NARRATIVE_LIMIT]


def _summary(result: PCAnalysisResult) -> str:
    d = result.dashboard
    direction = "증가" if (d.sales_delta_pct or 0) >= 0 else "감소"
    top_cat = d.sales_by_category[0].name if d.sales_by_category else "-"
    return (
        f"{result.meta.curr_label} 총매출은 {_won(d.total_sales_curr)}으로 전월 대비 "
        f"{abs(d.sales_delta_pct or 0)}% {direction}했습니다. "
        f"판매개수 {d.total_qty_curr:,.0f}개({d.qty_delta_pct}%), 평균 객단가 {_won(d.avg_price_curr)}, "
        f"판매 상품 수 {d.product_count_curr:,}개입니다. "
        f"매출 비중이 가장 큰 분류는 '{top_cat}'이며, 신규 {len(result.insights.new_products)}개·"
        f"판매중단 {len(result.insights.discontinued_products)}개 상품이 확인되었습니다."
    )


def _recommendations(result: PCAnalysisResult) -> list[str]:
    recs: list[str] = []
    ins = result.insights
    if ins.rising_top10:
        names = ", ".join(i.name for i in ins.rising_top10[:3])
        recs.append(f"상승세 상품({names})은 메인 노출·세트 구성으로 성장을 이어가세요.")
    if ins.falling_top10:
        names = ", ".join(i.name for i in ins.falling_top10[:3])
        recs.append(f"하락 상품({names})은 진열 위치·가격·품질을 점검해 원인을 규명하세요.")
    if ins.discontinued_products:
        recs.append(f"판매가 끊긴 {len(ins.discontinued_products)}개 상품이 품절인지 단종인지 확인하세요.")
    if ins.new_products:
        recs.append(f"신규 상품 {len(ins.new_products)}개의 안착 여부를 다음 달까지 추적하세요.")
    d = result.dashboard
    if (d.qty_delta_pct or 0) < 0 and (d.sales_delta_pct or 0) >= 0:
        recs.append("판매개수는 줄었는데 매출은 유지/증가했습니다. 객단가(가격) 상승 효과인지 확인하세요.")
    if not recs:
        recs.append("큰 변동이 없어 상위 매출 상품의 재고·품질 유지에 집중하세요.")
    return recs


def _rule_based(result: PCAnalysisResult) -> PCAIReport:
    products = _select(result)
    return PCAIReport(
        summary=_summary(result),
        product_narratives={p.name: _narrative_for(p) for p in products},
        recommendations=_recommendations(result),
        provider="rule-based",
    )


def _openai(result: PCAnalysisResult, api_key: str, model: str) -> PCAIReport:
    try:
        from openai import OpenAI
    except ImportError:
        return _rule_based(result)
    payload = {
        "period": {"prev": result.meta.prev_label, "curr": result.meta.curr_label},
        "dashboard": result.dashboard.model_dump(),
        "rising": [i.model_dump() for i in result.insights.rising_top10],
        "falling": [i.model_dump() for i in result.insights.falling_top10],
        "new": [i.model_dump() for i in result.insights.new_products[:5]],
        "discontinued": [i.model_dump() for i in result.insights.discontinued_products[:5]],
    }
    system = (
        "너는 PC방 매장의 상품 매출을 분석하는 데이터 분석가다. 숫자를 나열하지 말고 "
        "매출·판매개수·객단가·순위 변화의 '이유' 가설을 담은 한국어 스토리로 설명하라. "
        '반드시 JSON 으로만 답하라: {"summary": str, "product_narratives": {상품명: str}, "recommendations": [str]}'
    )
    try:
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
            temperature=0.4,
        )
        data = json.loads(resp.choices[0].message.content or "{}")
        return PCAIReport(
            summary=data.get("summary", ""),
            product_narratives=data.get("product_narratives", {}),
            recommendations=data.get("recommendations", []),
            provider="openai",
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("PC OpenAI 호출 실패(%s), 규칙기반 폴백", exc)
        return _rule_based(result)


def generate_pc_ai_report(result: PCAnalysisResult, api_key: str | None = None,
                          model: str = "gpt-4o-mini") -> PCAIReport:
    if api_key:
        return _openai(result, api_key, model)
    return _rule_based(result)
