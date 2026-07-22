"""AI 분석 내러티브 생성.

AI는 숫자를 그대로 읽지 않고 '스토리'를 만든다.
  - 실매출은 늘었는데 할인율은 줄었다 → 상품 경쟁력 상승 가능성
  - 주문건수·순위가 함께 하락 → 원인 확인 필요

OpenAI API 키가 설정되어 있으면 GPT로 풍부한 내러티브를 생성하고,
없으면 규칙 기반(rule-based) 폴백으로 동일한 구조의 스토리를 생성한다.
(MVP는 키 없이도 완전히 동작해야 하므로 폴백을 1차 시민으로 둔다.)
"""

from __future__ import annotations

import json
import logging

from app.models.schemas import AIReport, AnalysisResult, MenuAnalysis

logger = logging.getLogger(__name__)

# 내러티브를 생성할 후보 메뉴 상한(토큰/노이즈 관리)
_NARRATIVE_LIMIT = 12


def _fmt_won(value: float) -> str:
    return f"{value:,.0f}원"


# ---------------------------------------------------------------------------
# 규칙 기반 폴백
# ---------------------------------------------------------------------------
def _narrative_for(m: MenuAnalysis) -> str:
    """단일 메뉴에 대한 스토리형 서술."""
    g = m.sales_growth_pct
    o = m.order_growth_pct

    if m.is_new:
        return (
            f"{m.menu_name}은(는) 이번 달 신규로 진입해 실매출 {_fmt_won(m.curr.real_sales)}을 기록했습니다. "
            f"{m.curr.store_count}개 가맹점에서 판매되었으며 초기 반응을 지켜볼 필요가 있습니다."
        )
    if m.is_discontinued:
        prev_sales = m.prev.real_sales if m.prev else 0
        return (
            f"{m.menu_name}은(는) 전월 {_fmt_won(prev_sales)}의 매출이 있었으나 이번 달 판매가 중단되었습니다. "
            f"메뉴 개편 또는 재고/공급 이슈 여부를 확인해야 합니다."
        )
    if m.grew_without_discount:
        return (
            f"{m.menu_name}은(는) 전월보다 실매출이 {g}% 증가했습니다. "
            f"할인율은 오히려 {abs(m.discount_rate_delta)}%p 감소했습니다. "
            f"가격할인 효과가 아니라 상품 경쟁력이 상승했을 가능성이 있습니다."
        )
    if g is not None and g <= -20:
        rank_part = ""
        if m.rank_change is not None and m.rank_change < 0:
            rank_part = f" 순위도 {m.rank_prev}위에서 {m.rank_curr}위로 하락했습니다."
        order_part = f"주문건수가 {o}% 감소했고" if (o is not None and o < 0) else "실매출이 감소했고"
        return (
            f"{m.menu_name}은(는) {order_part} 실매출이 {g}% 줄었습니다.{rank_part} "
            f"원인 확인이 필요합니다."
        )
    if g is not None and g >= 20:
        disc = (
            "할인 확대가 성장에 기여했는지 함께 살펴볼 필요가 있습니다."
            if m.discount_rate_delta > 0.5
            else "할인 변화가 크지 않아 자연 수요 증가로 보입니다."
        )
        return f"{m.menu_name}은(는) 실매출이 {g}% 증가했습니다. {disc}"
    return (
        f"{m.menu_name}의 실매출은 전월 대비 {g}% 변동했습니다. "
        f"당월 기여도는 {m.contribution_pct}% 입니다."
    )


def _build_summary(result: AnalysisResult) -> str:
    d = result.dashboard
    direction = "증가" if (d.sales_delta_pct or 0) >= 0 else "감소"
    n_new = len(result.insights.new_menus)
    n_stop = len(result.insights.discontinued_menus)

    # 그룹별(주류/음식/기타) 흐름 한 줄 요약
    group_bits = []
    for g in d.sales_by_group:
        arrow = "↑" if (g.sales_delta_pct or 0) >= 0 else "↓"
        group_bits.append(
            f"{g.group} {_fmt_won(g.real_sales_curr)}(비중 {g.contribution_pct}%, {g.sales_delta_pct}% {arrow})"
        )
    group_line = " · ".join(group_bits)

    return (
        f"{result.meta.curr_label} 전체 실매출은 {_fmt_won(d.total_sales_curr)}으로 "
        f"전월 대비 {abs(d.sales_delta_pct or 0)}% {direction}했습니다. "
        f"주문건수는 {d.order_count_curr:,.0f}건({d.order_delta_pct}%), "
        f"이익률 {d.profit_rate_curr}%, 할인율 {d.discount_rate_curr}% 수준입니다. "
        f"그룹별로는 {group_line} 입니다. "
        f"신규 {n_new}개·판매중단 {n_stop}개 메뉴가 확인되었습니다."
    )


def _build_recommendations(result: AnalysisResult) -> list[str]:
    recs: list[str] = []
    ins = result.insights

    # 그룹(주류/음식) 상반된 흐름을 최우선으로 짚는다.
    groups = {g.group: g for g in result.dashboard.sales_by_group}
    liquor, food = groups.get("주류"), groups.get("음식")
    if liquor and food:
        ld, fd = liquor.sales_delta_pct or 0, food.sales_delta_pct or 0
        if ld * fd < 0:  # 방향이 반대
            up, down = ("주류", "음식") if ld > fd else ("음식", "주류")
            recs.append(
                f"{up}는 성장하고 {down}는 감소해 그룹 간 흐름이 엇갈립니다. "
                f"{down} 그룹의 하락 메뉴를 우선 점검하고, {up} 강세를 교차 판매(세트/페어링)로 연결하세요."
            )
        elif ld < 0 and fd < 0:
            recs.append("주류·음식 모두 매출이 감소했습니다. 방문객수(주문건수) 자체의 변화를 먼저 확인하세요.")
    if ins.grew_without_discount:
        names = ", ".join(i.menu_name for i in ins.grew_without_discount[:3])
        recs.append(f"할인 없이 성장한 메뉴({names})는 상품력이 검증된 만큼 대표 메뉴로 노출을 강화하세요.")
    if ins.falling_top10:
        names = ", ".join(i.menu_name for i in ins.falling_top10[:3])
        recs.append(f"하락 폭이 큰 메뉴({names})는 레시피/가격/노출 위치를 점검하고 원인을 규명하세요.")
    if ins.discontinued_menus:
        recs.append(f"판매 중단된 {len(ins.discontinued_menus)}개 메뉴가 공급 이슈인지 개편 의도인지 확인이 필요합니다.")
    if ins.new_menus:
        recs.append(f"신규 메뉴 {len(ins.new_menus)}개의 초기 반응을 2~3개월 추적해 안착 여부를 판단하세요.")
    if result.dashboard.discount_rate_curr > result.dashboard.discount_rate_prev + 0.2:
        recs.append("전체 할인율이 상승했습니다. 할인 의존도가 매출에 미치는 영향을 분리 분석하세요.")
    if not recs:
        recs.append("전월 대비 큰 변동이 없어, 상위 기여 메뉴의 재고·품질 유지에 집중하세요.")
    return recs


def _select_narrative_menus(result: AnalysisResult) -> list[MenuAnalysis]:
    """내러티브 생성 대상 메뉴 선별(중복 제거)."""
    codes: list[str] = []
    for group in (
        result.insights.rising_top10,
        result.insights.falling_top10,
        result.insights.grew_without_discount,
        result.insights.new_menus[:3],
        result.insights.discontinued_menus[:3],
    ):
        for item in group:
            if item.menu_code not in codes:
                codes.append(item.menu_code)
    by_code = {m.menu_code: m for m in result.menus}
    selected = [by_code[c] for c in codes if c in by_code]
    return selected[:_NARRATIVE_LIMIT]


def _rule_based_report(result: AnalysisResult) -> AIReport:
    menus = _select_narrative_menus(result)
    return AIReport(
        summary=_build_summary(result),
        menu_narratives={m.menu_code: _narrative_for(m) for m in menus},
        recommendations=_build_recommendations(result),
        provider="rule-based",
    )


# ---------------------------------------------------------------------------
# OpenAI 경로 (선택)
# ---------------------------------------------------------------------------
def _openai_report(result: AnalysisResult, api_key: str, model: str) -> AIReport:
    """GPT로 요약/추천을 생성. 실패 시 규칙 기반으로 폴백."""
    try:
        from openai import OpenAI
    except ImportError:  # pragma: no cover
        logger.warning("openai 패키지가 없어 규칙 기반으로 폴백합니다.")
        return _rule_based_report(result)

    # 프롬프트에는 요약에 필요한 핵심 지표만 압축해 전달한다.
    payload = {
        "period": {"prev": result.meta.prev_label, "curr": result.meta.curr_label},
        "dashboard": result.dashboard.model_dump(),
        "groups": [g.metrics.model_dump() for g in result.groups],
        "rising": [i.model_dump() for i in result.insights.rising_top10],
        "falling": [i.model_dump() for i in result.insights.falling_top10],
        "grew_without_discount": [i.model_dump() for i in result.insights.grew_without_discount],
        "new": [i.model_dump() for i in result.insights.new_menus[:5]],
        "discontinued": [i.model_dump() for i in result.insights.discontinued_menus[:5]],
    }
    system = (
        "너는 외식 프랜차이즈 메뉴개발팀을 돕는 데이터 분석가다. "
        "숫자를 그대로 나열하지 말고 '왜 그런지' 가설을 담은 한국어 스토리로 설명하라. "
        "특히 실매출이 늘었는데 할인율이 줄었다면 상품 경쟁력 상승 가능성을, "
        "주문·순위가 함께 하락하면 원인 점검 필요를 지적하라. "
        "반드시 아래 JSON 스키마로만 답하라: "
        '{"summary": str, "menu_narratives": {menu_code: str}, "recommendations": [str]}'
    )
    try:
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            temperature=0.4,
        )
        data = json.loads(resp.choices[0].message.content or "{}")
        return AIReport(
            summary=data.get("summary", ""),
            menu_narratives=data.get("menu_narratives", {}),
            recommendations=data.get("recommendations", []),
            provider="openai",
        )
    except Exception as exc:  # noqa: BLE001 - 외부 API 실패는 폴백으로 흡수
        logger.warning("OpenAI 호출 실패(%s). 규칙 기반으로 폴백합니다.", exc)
        return _rule_based_report(result)


def generate_ai_report(
    result: AnalysisResult,
    api_key: str | None = None,
    model: str = "gpt-4o-mini",
) -> AIReport:
    """분석 결과에 AI 내러티브를 생성해 :class:`AIReport` 반환.

    api_key 가 없으면 규칙 기반 폴백을 사용한다(오프라인 동작 보장).
    """
    if api_key:
        return _openai_report(result, api_key, model)
    return _rule_based_report(result)
