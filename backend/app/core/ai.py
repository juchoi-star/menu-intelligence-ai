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
# 분석 컨텍스트 (계절·분류평균·매장수) — 근거 있는 가설을 만들기 위한 재료
# ---------------------------------------------------------------------------
# 계절 수요가 뚜렷한 메뉴 키워드. 이름에 포함되면 그 계절 상품으로 추정한다.
# (단정하지 않고 "계절 효과 가능성"으로만 서술한다)
_SEASON_KEYWORDS: dict[str, tuple[str, ...]] = {
    "여름": (
        "화채", "빙수", "슬러시", "샤베트", "아이스", "냉면", "냉모밀", "메밀", "물회",
        "콩국수", "에이드", "수박", "참외", "토마토", "오이", "얼음", "하이볼",
        "생맥주", "레몬", "자몽", "스무디", "청포도",
    ),
    "겨울": (
        "탕", "국물", "어묵", "우동", "전골", "찌개", "라면", "호떡", "군고구마",
        "따뜻", "정종", "사케", "국밥", "죽", "핫",
    ),
    "봄": ("미나리", "부추", "딸기", "쑥", "나물", "벚"),
    "가을": ("대하", "전어", "밤", "고구마", "국화", "버섯"),
}

_MONTH_SEASON = {
    3: "봄", 4: "봄", 5: "봄",
    6: "여름", 7: "여름", 8: "여름",
    9: "가을", 10: "가을", 11: "가을",
    12: "겨울", 1: "겨울", 2: "겨울",
}

# 당월 계절에 붙일 날씨 표현
_SEASON_PHRASE = {
    "여름": "기온이 오르는",
    "겨울": "날이 추워지는",
    "봄": "날이 풀리는",
    "가을": "날이 선선해지는",
}


def _season_of(month: int | None) -> str | None:
    return _MONTH_SEASON.get(month) if month else None


def _season_tag(menu_name: str) -> str | None:
    """메뉴명에서 계절 상품 성격을 추정. 해당 없으면 None."""
    for season, words in _SEASON_KEYWORDS.items():
        if any(w in menu_name for w in words):
            return season
    return None


class _Ctx:
    """내러티브 작성에 쓰는 전월/당월 맥락(계절, 분류 평균, 매장수)."""

    def __init__(self, result: AnalysisResult) -> None:
        meta = result.meta
        self.curr_month = meta.curr_period_start.month if meta.curr_period_start else None
        self.prev_month = meta.prev_period_start.month if meta.prev_period_start else None
        self.curr_season = _season_of(self.curr_month)
        self.prev_season = _season_of(self.prev_month)
        self.store_total = meta.store_count
        self.total_growth = result.dashboard.sales_delta_pct

        # 분류별 합계 성장률 — 같은 분류 흐름 대비 상대 성과를 판단하는 기준
        cur: dict[str, float] = {}
        prv: dict[str, float] = {}
        for m in result.menus:
            cur[m.category] = cur.get(m.category, 0.0) + m.curr.real_sales
            prv[m.category] = prv.get(m.category, 0.0) + (m.prev.real_sales if m.prev else 0.0)
        self.cat_growth: dict[str, float | None] = {
            cat: (round((c - prv.get(cat, 0.0)) / prv[cat] * 100.0, 1) if prv.get(cat) else None)
            for cat, c in cur.items()
        }


def _price_volume_split(m: MenuAnalysis) -> tuple[float, float] | None:
    """매출 증감을 수량효과·단가효과로 분해.

    건당 실매출 P = 실매출/주문건수 로 두면
        Δ매출 = P0·(Q1-Q0)  [수량효과]  +  Q1·(P1-P0)  [단가효과]
    어느 쪽이 변화를 주도했는지 판단하는 근거가 된다.
    """
    if not m.prev or not m.prev.order_count or not m.curr.order_count:
        return None
    p0 = m.prev.real_sales / m.prev.order_count
    p1 = m.curr.real_sales / m.curr.order_count
    return p0 * (m.curr.order_count - m.prev.order_count), m.curr.order_count * (p1 - p0)


def _season_clause(m: MenuAnalysis, ctx: _Ctx, rising: bool) -> str | None:
    """계절 효과 가설. 메뉴의 계절성과 증감 방향이 맞을 때만 붙인다."""
    tag = _season_tag(m.menu_name)
    if not tag or not ctx.curr_season:
        return None
    weather = _SEASON_PHRASE.get(ctx.curr_season, "")
    month = f"{ctx.curr_month}월" if ctx.curr_month else "당월"
    if tag == ctx.curr_season and rising:
        # 예: 6월(여름)에 화채가 상승 → 계절 수요
        return f"{weather} {month}로 접어들며 {tag} 메뉴 수요가 늘어난 계절 효과로 보입니다"
    if tag != ctx.curr_season and not rising and tag == ctx.prev_season:
        # 예: 5월(봄) 상품이 6월에 하락 → 계절이 지남
        return f"{tag} 시즌이 지나며 자연 감소한 계절 효과일 수 있습니다"
    if tag != ctx.curr_season and not rising:
        return f"{weather} {month} 날씨와 {tag} 메뉴 특성이 맞지 않아 수요가 줄어든 것으로 보입니다"
    return None


def _driver_clause(m: MenuAnalysis) -> str | None:
    """무엇이 매출 변화를 주도했는지(판매량 vs 단가)."""
    split = _price_volume_split(m)
    if not split:
        return None
    vol, price = split
    if abs(vol) < 1 and abs(price) < 1:
        return None
    # 주도 요인이 뚜렷할 때만(한쪽이 2배 이상) 언급
    if abs(vol) >= abs(price) * 2:
        return (
            f"판매 건수 자체가 늘어난 것이 주된 요인입니다"
            if vol > 0
            else "판매 건수 감소가 주된 요인입니다"
        )
    if abs(price) >= abs(vol) * 2:
        return (
            "건당 금액(가격·구성) 상승이 매출을 끌어올렸습니다"
            if price > 0
            else "건당 금액이 낮아진 것이 매출 감소로 이어졌습니다"
        )
    return (
        "판매 건수와 건당 금액이 함께 움직였습니다"
        if vol * price > 0
        else "판매 건수와 건당 금액이 서로 반대로 움직여 상쇄되었습니다"
    )


def _store_clause(m: MenuAnalysis, ctx: _Ctx, rising: bool) -> str | None:
    """판매 매장수 변화 — 매장 확산 효과와 매장당 판매력을 구분해준다.

    매출 방향과 매장수 방향을 함께 봐야 한다. 매장이 줄었는데 매출이 늘었다면
    '매장 감소 영향'이 아니라 오히려 매장당 판매력이 좋아진 신호다.
    """
    curr_n = m.curr.store_count
    prev_n = m.prev.store_count if m.prev else 0
    if prev_n and curr_n > prev_n:
        return (
            f"판매 매장이 {prev_n}개→{curr_n}개로 늘어난 영향도 함께 있습니다"
            if rising
            else f"판매 매장은 {prev_n}개→{curr_n}개로 늘었는데 매출은 줄어 매장당 판매력 저하를 점검해야 합니다"
        )
    if prev_n and curr_n < prev_n:
        return (
            f"판매 매장이 {prev_n}개→{curr_n}개로 줄었는데도 매출이 늘어 매장당 판매력이 개선됐습니다"
            if rising
            else f"판매 매장이 {prev_n}개→{curr_n}개로 줄어든 영향이 큽니다"
        )
    if ctx.store_total and curr_n and curr_n <= ctx.store_total * 0.6:
        return (
            f"전체 {ctx.store_total}개 중 {curr_n}개 매장에서만 판매돼 "
            f"미판매 매장으로 확대할 여지가 있습니다"
        )
    return None


def _relative_clause(m: MenuAnalysis, ctx: _Ctx) -> str | None:
    """같은 분류 흐름 대비 상대 성과 — 메뉴 고유 요인인지 분류 전체 흐름인지 구분."""
    g = m.sales_growth_pct
    cg = ctx.cat_growth.get(m.category)
    if g is None or cg is None or abs(g - cg) < 10:
        return None
    if g > cg:
        return (
            f"같은 '{m.category}' 분류 전체가 {cg}% 인 것에 비하면 두드러진 성과입니다"
            if cg <= 0
            else f"'{m.category}' 분류 평균({cg}%)을 웃도는 성과입니다"
        )
    return (
        f"'{m.category}' 분류 전체는 {cg}% 인데 이 메뉴만 부진해 메뉴 자체 요인을 살펴야 합니다"
        if cg > 0
        else f"'{m.category}' 분류 전반({cg}%)의 부진과 같은 흐름입니다"
    )


def _join(head: str, clauses: list[str | None], limit: int = 3) -> str:
    """본문 + 근거 절들을 자연스러운 한 문단으로 합친다."""
    picked = [c for c in clauses if c][:limit]
    if not picked:
        return head
    return head + " " + ". ".join(picked) + "."


# ---------------------------------------------------------------------------
# 규칙 기반 폴백
# ---------------------------------------------------------------------------
def _narrative_for(m: MenuAnalysis, ctx: _Ctx | None = None) -> str:
    """단일 메뉴에 대한 스토리형 서술.

    숫자 나열이 아니라 '왜 그런지'를 여러 근거(계절·판매량/단가·매장 확산·
    분류 대비 상대 성과·할인)로 조합해 매번 다른 각도의 설명을 만든다.
    """
    g = m.sales_growth_pct
    o = m.order_growth_pct

    if m.is_new:
        season = None
        if ctx:
            tag = _season_tag(m.menu_name)
            if tag and tag == ctx.curr_season:
                season = f"{tag} 시즌에 맞춰 투입된 것으로 보여 시즌 종료 후 수요 변화를 함께 확인하세요"
        return _join(
            f"{m.menu_name}은(는) 이번 달 신규로 진입해 실매출 {_fmt_won(m.curr.real_sales)}을 "
            f"{m.curr.store_count}개 가맹점에서 기록했습니다.",
            [season, "초기 반응이므로 2~3개월 추적해 안착 여부를 판단해야 합니다"],
            limit=2,
        )

    if m.is_discontinued:
        prev_sales = m.prev.real_sales if m.prev else 0
        return _join(
            f"{m.menu_name}은(는) 전월 {_fmt_won(prev_sales)}의 매출이 있었으나 이번 달 판매가 중단되었습니다.",
            ["메뉴 개편 의도인지 공급·재고 이슈인지 확인이 필요합니다"],
            limit=1,
        )

    rising = (g or 0) >= 0
    clauses: list[str | None] = []

    # 1) 계절 효과(메뉴 성격과 증감 방향이 맞을 때만)
    if ctx:
        clauses.append(_season_clause(m, ctx, rising))
    # 2) 무엇이 주도했나 — 판매량 vs 건당 금액
    clauses.append(_driver_clause(m))
    # 3) 매장 확산/축소 효과
    if ctx:
        clauses.append(_store_clause(m, ctx, rising))
    # 4) 같은 분류 흐름 대비 상대 성과
    if ctx:
        clauses.append(_relative_clause(m, ctx))
    # 5) 할인 영향
    if m.grew_without_discount:
        clauses.append(
            f"할인율이 오히려 {abs(m.discount_rate_delta)}%p 낮아졌는데도 성장해 "
            f"가격 할인이 아닌 상품력 자체가 작용한 것으로 보입니다"
        )
    elif m.discount_rate_delta > 0.5 and rising:
        clauses.append(f"할인율이 {m.discount_rate_delta}%p 올라 할인 기여분을 분리해 볼 필요가 있습니다")
    # 6) 순위 변화
    if m.rank_change:
        if m.rank_change < 0:
            clauses.append(f"그룹 내 순위도 {m.rank_prev}위에서 {m.rank_curr}위로 밀렸습니다")
        elif m.rank_change >= 3:
            clauses.append(f"그룹 내 순위가 {m.rank_prev}위에서 {m.rank_curr}위로 올랐습니다")

    order_bit = (
        f", 주문건수는 {abs(o)}% " + ("증가" if o >= 0 else "감소") if o is not None else ""
    )
    head = (
        f"{m.menu_name}은(는) 전월 대비 실매출이 {abs(g) if g is not None else 0}% "
        f"{'증가' if rising else '감소'}({_fmt_won(m.curr.real_sales)}){order_bit}했습니다."
    )
    return _join(head, clauses)


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


def _seasonal_recommendation(result: AnalysisResult) -> str | None:
    """계절 흐름에 맞춘 제안 — 다음 달 시즌 메뉴를 미리 준비하도록."""
    ctx = _Ctx(result)
    if not ctx.curr_month or not ctx.curr_season:
        return None
    next_month = ctx.curr_month % 12 + 1
    next_season = _season_of(next_month)

    # 당월 계절 상품이 실제로 성장했는지 데이터로 확인
    season_rising = [
        i.menu_name
        for i in result.insights.rising_top10
        if _season_tag(i.menu_name) == ctx.curr_season
    ]
    if season_rising:
        names = ", ".join(season_rising[:3])
        base = (
            f"{ctx.curr_month}월 {ctx.curr_season} 메뉴({names})가 상승세입니다. "
            f"{_SEASON_PHRASE.get(ctx.curr_season, '')} 시기에 맞춰 노출·재고를 선제적으로 확대하세요."
        )
        if next_season and next_season != ctx.curr_season:
            base += f" {next_month}월부터는 {next_season} 메뉴로 전환 준비도 함께 검토하세요."
        return base

    season_falling = [
        i.menu_name
        for i in result.insights.falling_top10
        if _season_tag(i.menu_name) and _season_tag(i.menu_name) != ctx.curr_season
    ]
    if season_falling:
        names = ", ".join(season_falling[:3])
        return (
            f"철이 지난 메뉴({names})의 하락은 계절 요인일 수 있습니다. "
            f"메뉴 자체 문제와 구분해 판단하고, {ctx.curr_season} 대체 메뉴 배치를 검토하세요."
        )
    return None


def _build_recommendations(result: AnalysisResult) -> list[str]:
    recs: list[str] = []
    ins = result.insights

    seasonal = _seasonal_recommendation(result)
    if seasonal:
        recs.append(seasonal)

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
    ctx = _Ctx(result)
    return AIReport(
        summary=_build_summary(result),
        menu_narratives={m.menu_code: _narrative_for(m, ctx) for m in menus},
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
