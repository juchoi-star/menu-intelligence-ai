"""메뉴/가맹점 비교 분석 엔진.

전월(prev)·당월(curr) 두 :class:`ParsedFile` 을 받아
성장률·순위변화·기여도·할인율·이익률·신규/중단 메뉴·가맹점 지표를
계산해 :class:`AnalysisResult`(AI 내러티브 제외)를 구성한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.core.groups import GROUP_ORDER, group_for
from app.core.parser import MenuRecord, ParsedFile
from app.core.text import canonical_key, display_name
from app.models.schemas import (
    AnalysisMeta,
    AnalysisResult,
    AIReport,
    CategorySales,
    Dashboard,
    GroupSlice,
    GroupSummary,
    Insights,
    MenuAnalysis,
    MenuInsightItem,
    MonthlyPoint,
    PeriodMetrics,
    StoreAnalysis,
    StoreDelta,
)

# --- 분석 파라미터 -----------------------------------------------------------
TOP_N = 10
MIN_BASE_SALES = 100_000    # 상승/하락 TOP 노이즈 방지용 최소 기준 매출
MIN_GROWTH_SALES = 50_000   # 할인없이 성장 후보 최소 당월 매출


# ---------------------------------------------------------------------------
# 수치 헬퍼
# ---------------------------------------------------------------------------
def _is_unknown(code: str) -> bool:
    """이름 미상(POS가 코드/명 비운) 메뉴인지. 순위·인사이트에서 제외 대상."""
    return code.startswith("UNKNOWN-")


def _period_warning(prev: ParsedFile, curr: ParsedFile) -> str | None:
    """전월/당월 조회기간 길이가 크게 다르면 경고(예: 31일 vs 6일 → 증감률 왜곡)."""
    if not (prev.period_start and prev.period_end and curr.period_start and curr.period_end):
        return None
    pd = (prev.period_end - prev.period_start).days + 1
    cd = (curr.period_end - curr.period_start).days + 1
    if pd <= 0 or cd <= 0:
        return None
    if min(pd, cd) / max(pd, cd) < 0.9:  # 10% 이상 차이
        return (
            f"⚠️ 비교 기간이 다릅니다 — 전월 {pd}일({prev.period_start}~{prev.period_end}) vs "
            f"당월 {cd}일({curr.period_start}~{curr.period_end}). 기간이 다르면 증감률이 크게 왜곡됩니다. "
            f"같은 길이(예: 각 월 1일~말일 전체)로 맞춰 다시 올려주세요."
        )
    return None


def _safe_div(num: float, den: float) -> float:
    return num / den if den else 0.0


def _pct_change(curr: float, prev: float) -> float | None:
    """증감률(%). 전월이 0이면 계산 불가로 None."""
    if prev == 0:
        return None
    return (curr - prev) / prev * 100.0


def _round(value: float | None, ndigits: int = 2) -> float | None:
    return round(value, ndigits) if value is not None else None


# ---------------------------------------------------------------------------
# 집계 컨테이너
# ---------------------------------------------------------------------------
@dataclass
class _StoreLeg:
    store_name: str
    real_sales: float = 0.0
    order_count: float = 0.0


@dataclass
class _MenuAgg:
    """체인 전체로 합산한 메뉴 단위 집계(한 달치)."""

    menu_code: str
    menu_name: str
    category: str
    group: str = "기타"
    key: str = ""          # 취합/매칭 키(정규화 이름)
    unit_price: float = 0.0
    order_count: float = 0.0
    order_amount: float = 0.0
    discount_amount: float = 0.0
    real_sales: float = 0.0
    net_sales: float = 0.0
    cogs: float = 0.0
    gross_profit: float = 0.0
    stores: dict[str, _StoreLeg] = field(default_factory=dict)

    def add(self, rec: MenuRecord) -> None:
        self.order_count += rec.order_count
        self.order_amount += rec.order_amount
        self.discount_amount += rec.discount_amount
        self.real_sales += rec.real_sales
        self.net_sales += rec.net_sales
        self.cogs += rec.cogs
        self.gross_profit += rec.gross_profit
        if rec.unit_price:
            self.unit_price = rec.unit_price
        leg = self.stores.setdefault(rec.store_code, _StoreLeg(rec.store_name))
        leg.real_sales += rec.real_sales
        leg.order_count += rec.order_count

    def metrics(self) -> PeriodMetrics:
        return PeriodMetrics(
            order_count=self.order_count,
            order_amount=self.order_amount,
            discount_amount=self.discount_amount,
            real_sales=self.real_sales,
            net_sales=self.net_sales,
            cogs=self.cogs,
            gross_profit=self.gross_profit,
            store_count=len(self.stores),
        )

    def discount_rate(self) -> float:
        return _safe_div(self.discount_amount, self.order_amount) * 100.0

    def profit_rate(self) -> float:
        return _safe_div(self.gross_profit, self.real_sales) * 100.0


def _aggregate_menus(
    records: list[MenuRecord], alias_map: dict[str, str] | None = None
) -> dict[str, _MenuAgg]:
    """정규화 이름(+별칭표) 기준으로 체인 전체 집계(같은 이름·다른 코드도 합침).

    대표 표시명/코드/분류는 매출이 가장 큰 레코드 기준으로 선택한다.
    """
    out: dict[str, _MenuAgg] = {}
    rep: dict[str, tuple] = {}  # key -> (best_sales, name, code, category)
    for rec in records:
        key = canonical_key(rec.menu_name, alias_map) or rec.menu_code
        agg = out.get(key)
        if agg is None:
            agg = _MenuAgg(
                menu_code=rec.menu_code,
                menu_name=rec.menu_name,
                category=rec.category,
                group=group_for(rec.category),
                key=key,
            )
            out[key] = agg
            rep[key] = (-1.0, rec.menu_name, rec.menu_code, rec.category)
        agg.add(rec)
        if rec.real_sales > rep[key][0]:
            rep[key] = (rec.real_sales, rec.menu_name, rec.menu_code, rec.category)
    for key, agg in out.items():
        _, name, code, cat = rep[key]
        agg.menu_name = display_name(name, alias_map)  # 별칭 대표명 우선
        agg.menu_code = code
        agg.category = cat
        agg.group = group_for(cat)
    return out


def _rank_map(aggs: dict[str, _MenuAgg]) -> dict[str, int]:
    """그룹 내 실매출 내림차순 순위(1-based). 실매출 0 은 순위 미부여.

    주류/음식/기타는 성격이 달라 그룹 내에서만 순위를 매긴다
    (참이슬과 김치전을 한 순위표에 두지 않는다).
    """
    ranks: dict[str, int] = {}
    by_group: dict[str, list[_MenuAgg]] = {}
    for a in aggs.values():
        if a.real_sales > 0 and not _is_unknown(a.menu_code):  # 미상은 순위 미부여
            by_group.setdefault(a.group, []).append(a)
    for members in by_group.values():
        members.sort(key=lambda a: a.real_sales, reverse=True)
        for i, a in enumerate(members):
            ranks[a.key] = i + 1  # 집계 키(정규화 이름) 기준
    return ranks


def _group_totals(aggs: dict[str, _MenuAgg]) -> dict[str, float]:
    """그룹별 실매출 합계."""
    totals: dict[str, float] = {}
    for a in aggs.values():
        totals[a.group] = totals.get(a.group, 0.0) + a.real_sales
    return totals


# ---------------------------------------------------------------------------
# 메뉴 분석
# ---------------------------------------------------------------------------
def _build_menu_analyses(
    prev_aggs: dict[str, _MenuAgg],
    curr_aggs: dict[str, _MenuAgg],
) -> list[MenuAnalysis]:
    prev_rank = _rank_map(prev_aggs)
    curr_rank = _rank_map(curr_aggs)
    total_curr_real = sum(a.real_sales for a in curr_aggs.values())
    group_curr_real = _group_totals(curr_aggs)  # 그룹 내 기여도 분모

    all_codes = set(prev_aggs) | set(curr_aggs)
    analyses: list[MenuAnalysis] = []

    for code in all_codes:
        cur = curr_aggs.get(code)
        prv = prev_aggs.get(code)
        ref = cur or prv
        assert ref is not None

        cur_real = cur.real_sales if cur else 0.0
        prv_real = prv.real_sales if prv else 0.0
        cur_orders = cur.order_count if cur else 0.0
        prv_orders = prv.order_count if prv else 0.0

        disc_curr = cur.discount_rate() if cur else 0.0
        disc_prev = prv.discount_rate() if prv else 0.0

        is_new = prv is None or prv_real == 0
        is_discontinued = cur is None or cur_real == 0

        sales_growth = _pct_change(cur_real, prv_real)
        grew_without_discount = (
            not is_new
            and sales_growth is not None
            and sales_growth > 0
            and (disc_curr - disc_prev) <= 0.01
            and cur_real >= MIN_GROWTH_SALES
        )

        rc = curr_rank.get(code)
        rp = prev_rank.get(code)
        rank_change = (rp - rc) if (rc is not None and rp is not None) else None

        # 가맹점별 증감표 구성
        store_codes = set()
        if cur:
            store_codes |= set(cur.stores)
        if prv:
            store_codes |= set(prv.stores)
        by_store: list[StoreDelta] = []
        for sc in store_codes:
            cleg = cur.stores.get(sc) if cur else None
            pleg = prv.stores.get(sc) if prv else None
            name = (cleg or pleg).store_name  # type: ignore[union-attr]
            c_rs = cleg.real_sales if cleg else 0.0
            p_rs = pleg.real_sales if pleg else 0.0
            c_or = cleg.order_count if cleg else 0.0
            p_or = pleg.order_count if pleg else 0.0
            by_store.append(
                StoreDelta(
                    store_code=sc,
                    store_name=name,
                    curr_real_sales=c_rs,
                    prev_real_sales=p_rs,
                    sales_delta_pct=_round(_pct_change(c_rs, p_rs)),
                    curr_orders=c_or,
                    prev_orders=p_or,
                    orders_delta_pct=_round(_pct_change(c_or, p_or)),
                )
            )
        by_store.sort(key=lambda s: s.curr_real_sales, reverse=True)

        analyses.append(
            MenuAnalysis(
                menu_code=ref.menu_code,
                menu_name=ref.menu_name,
                category=ref.category,
                group=ref.group,
                unit_price=ref.unit_price,
                curr=cur.metrics() if cur else PeriodMetrics(),
                prev=prv.metrics() if prv else None,
                sales_growth_pct=_round(sales_growth),
                order_growth_pct=_round(_pct_change(cur_orders, prv_orders)),
                sales_delta_abs=cur_real - prv_real,
                discount_rate_curr=round(disc_curr, 2),
                discount_rate_prev=round(disc_prev, 2),
                discount_rate_delta=round(disc_curr - disc_prev, 2),
                profit_rate_curr=round(cur.profit_rate() if cur else 0.0, 2),
                profit_rate_prev=round(prv.profit_rate() if prv else 0.0, 2),
                rank_curr=rc,
                rank_prev=rp,
                rank_change=rank_change,
                contribution_pct=round(_safe_div(cur_real, group_curr_real.get(ref.group, 0.0)) * 100.0, 2),
                contribution_overall_pct=round(_safe_div(cur_real, total_curr_real) * 100.0, 2),
                is_new=is_new,
                is_discontinued=is_discontinued,
                grew_without_discount=grew_without_discount,
                by_store=by_store,
            )
        )

    # 기본 정렬: 당월 실매출 내림차순
    analyses.sort(key=lambda m: m.curr.real_sales, reverse=True)
    return analyses


# ---------------------------------------------------------------------------
# 인사이트(상승/하락/순위/신규 등)
# ---------------------------------------------------------------------------
def _to_item(m: MenuAnalysis, value: float | None, detail: str = "") -> MenuInsightItem:
    return MenuInsightItem(
        menu_code=m.menu_code,
        menu_name=m.menu_name,
        category=m.category,
        value=_round(value),
        curr_real_sales=m.curr.real_sales,
        prev_real_sales=m.prev.real_sales if m.prev else 0.0,
        detail=detail,
    )


def _build_insights(menus: list[MenuAnalysis]) -> Insights:
    # 상승/하락: 신규/중단 제외 + 최소 기준매출 이상만
    growth_pool = [
        m
        for m in menus
        if not m.is_new
        and not m.is_discontinued
        and m.sales_growth_pct is not None
        and (m.prev.real_sales if m.prev else 0) >= MIN_BASE_SALES
    ]
    rising = sorted(growth_pool, key=lambda m: m.sales_growth_pct or 0, reverse=True)[:TOP_N]
    falling = sorted(growth_pool, key=lambda m: m.sales_growth_pct or 0)[:TOP_N]

    contributors = sorted(menus, key=lambda m: m.curr.real_sales, reverse=True)[:TOP_N]

    order_pool = [
        m
        for m in menus
        if not m.is_new and not m.is_discontinued and m.order_growth_pct is not None
        and (m.prev.order_count if m.prev else 0) >= 30
    ]
    order_top = sorted(order_pool, key=lambda m: m.order_growth_pct or 0, reverse=True)[:TOP_N]

    rank_pool = [m for m in menus if m.rank_change is not None]
    rank_up = sorted(
        (m for m in rank_pool if (m.rank_change or 0) > 0),
        key=lambda m: m.rank_change or 0,
        reverse=True,
    )[:TOP_N]
    rank_down = sorted(
        (m for m in rank_pool if (m.rank_change or 0) < 0),
        key=lambda m: m.rank_change or 0,
    )[:TOP_N]

    new_menus = sorted(
        (m for m in menus if m.is_new and m.curr.real_sales > 0),
        key=lambda m: m.curr.real_sales,
        reverse=True,
    )
    discontinued = sorted(
        (m for m in menus if m.is_discontinued and m.prev and m.prev.real_sales > 0),
        key=lambda m: m.prev.real_sales if m.prev else 0,
        reverse=True,
    )
    gwd = sorted(
        (m for m in menus if m.grew_without_discount),
        key=lambda m: m.sales_growth_pct or 0,
        reverse=True,
    )[:TOP_N]

    return Insights(
        rising_top10=[_to_item(m, m.sales_growth_pct, f"실매출 {m.sales_growth_pct}% ↑") for m in rising],
        falling_top10=[_to_item(m, m.sales_growth_pct, f"실매출 {m.sales_growth_pct}% ↓") for m in falling],
        top_contributors=[_to_item(m, m.contribution_pct, f"기여도 {m.contribution_pct}%") for m in contributors],
        order_growth_top=[_to_item(m, m.order_growth_pct, f"주문 {m.order_growth_pct}% ↑") for m in order_top],
        rank_up=[_to_item(m, m.rank_change, f"{m.rank_prev}위 → {m.rank_curr}위") for m in rank_up],
        rank_down=[_to_item(m, m.rank_change, f"{m.rank_prev}위 → {m.rank_curr}위") for m in rank_down],
        new_menus=[_to_item(m, m.curr.real_sales, "신규 진입") for m in new_menus],
        discontinued_menus=[_to_item(m, m.prev.real_sales if m.prev else 0, "판매 중단") for m in discontinued],
        grew_without_discount=[
            _to_item(m, m.sales_growth_pct, f"할인율 {m.discount_rate_delta}%p, 매출 {m.sales_growth_pct}% ↑")
            for m in gwd
        ],
    )


# ---------------------------------------------------------------------------
# 그룹(주류/음식/기타) 요약
# ---------------------------------------------------------------------------
def _category_sales(menus: list[MenuAnalysis]) -> list[CategorySales]:
    """메뉴 부분집합에서 분류별 당월/전월 실매출 집계."""
    acc: dict[str, list] = {}
    for m in menus:
        e = acc.setdefault(m.category, [0.0, 0.0, m.group])
        e[0] += m.curr.real_sales
        e[1] += m.prev.real_sales if m.prev else 0.0
    return sorted(
        (
            CategorySales(
                category=k, group=v[2], curr=v[0], prev=v[1],
                delta_pct=_round(_pct_change(v[0], v[1])),
            )
            for k, v in acc.items()
        ),
        key=lambda c: c.curr,
        reverse=True,
    )


def _group_slice(group: str, menus: list[MenuAnalysis], total_curr_real: float) -> GroupSlice:
    cur_sales = sum(m.curr.real_sales for m in menus)
    prev_sales = sum((m.prev.real_sales if m.prev else 0.0) for m in menus)
    cur_orders = sum(m.curr.order_count for m in menus)
    prev_orders = sum((m.prev.order_count if m.prev else 0.0) for m in menus)
    cur_oa = sum(m.curr.order_amount for m in menus)
    prev_oa = sum((m.prev.order_amount if m.prev else 0.0) for m in menus)
    cur_disc = sum(m.curr.discount_amount for m in menus)
    prev_disc = sum((m.prev.discount_amount if m.prev else 0.0) for m in menus)
    cur_gp = sum(m.curr.gross_profit for m in menus)
    return GroupSlice(
        group=group,
        real_sales_curr=cur_sales,
        real_sales_prev=prev_sales,
        sales_delta_pct=_round(_pct_change(cur_sales, prev_sales)),
        order_count_curr=cur_orders,
        order_count_prev=prev_orders,
        order_delta_pct=_round(_pct_change(cur_orders, prev_orders)),
        profit_rate_curr=round(_safe_div(cur_gp, cur_sales) * 100.0, 2),
        discount_rate_curr=round(_safe_div(cur_disc, cur_oa) * 100.0, 2),
        discount_rate_prev=round(_safe_div(prev_disc, prev_oa) * 100.0, 2),
        menu_count_curr=sum(1 for m in menus if m.curr.real_sales > 0),
        contribution_pct=round(_safe_div(cur_sales, total_curr_real) * 100.0, 2),
    )


def _build_group_summaries(
    menus: list[MenuAnalysis], total_curr_real: float
) -> tuple[list[GroupSummary], list[GroupSlice]]:
    """그룹별(주류/음식/기타) 요약 + 대시보드용 슬라이스 목록 생성."""
    summaries: list[GroupSummary] = []
    slices: list[GroupSlice] = []
    for group in GROUP_ORDER:
        members = [m for m in menus if m.group == group]
        if not members:
            continue
        slice_ = _group_slice(group, members, total_curr_real)  # 지표는 미상 포함(그룹합=총합)
        slices.append(slice_)
        ranked = [m for m in members if not _is_unknown(m.menu_code)]  # 순위·인사이트는 미상 제외
        summaries.append(
            GroupSummary(
                group=group,
                metrics=slice_,
                sales_by_category=_category_sales(members),
                insights=_build_insights(ranked),
            )
        )
    return summaries, slices


# ---------------------------------------------------------------------------
# 가맹점 분석
# ---------------------------------------------------------------------------
@dataclass
class _StoreAgg:
    store_code: str
    store_name: str
    real_sales: float = 0.0
    order_count: float = 0.0
    order_amount: float = 0.0
    discount_amount: float = 0.0
    gross_profit: float = 0.0
    menus: set[str] = field(default_factory=set)
    group_sales: dict[str, float] = field(default_factory=dict)  # 그룹별 실매출

    def add(self, rec: MenuRecord) -> None:
        self.real_sales += rec.real_sales
        self.order_count += rec.order_count
        self.order_amount += rec.order_amount
        self.discount_amount += rec.discount_amount
        self.gross_profit += rec.gross_profit
        self.menus.add(rec.menu_code)
        g = group_for(rec.category)
        self.group_sales[g] = self.group_sales.get(g, 0.0) + rec.real_sales


def _aggregate_stores(records: list[MenuRecord]) -> dict[str, _StoreAgg]:
    out: dict[str, _StoreAgg] = {}
    for rec in records:
        agg = out.get(rec.store_code)
        if agg is None:
            agg = _StoreAgg(rec.store_code, rec.store_name)
            out[rec.store_code] = agg
        agg.add(rec)
    return out


def _build_store_analyses(
    prev: dict[str, _StoreAgg], curr: dict[str, _StoreAgg]
) -> list[StoreAnalysis]:
    out: list[StoreAnalysis] = []
    for sc in set(prev) | set(curr):
        c = curr.get(sc)
        p = prev.get(sc)
        ref = c or p
        assert ref is not None
        c_sales = c.real_sales if c else 0.0
        p_sales = p.real_sales if p else 0.0
        out.append(
            StoreAnalysis(
                store_code=sc,
                store_name=ref.store_name,
                real_sales_curr=c_sales,
                real_sales_prev=p_sales,
                sales_delta_pct=_round(_pct_change(c_sales, p_sales)),
                order_count_curr=c.order_count if c else 0.0,
                order_count_prev=p.order_count if p else 0.0,
                order_delta_pct=_round(
                    _pct_change(c.order_count if c else 0.0, p.order_count if p else 0.0)
                ),
                gross_profit_curr=c.gross_profit if c else 0.0,
                profit_rate_curr=round(_safe_div(c.gross_profit, c.real_sales) * 100.0, 2) if c else 0.0,
                discount_rate_curr=round(_safe_div(c.discount_amount, c.order_amount) * 100.0, 2) if c else 0.0,
                menu_count_curr=len(c.menus) if c else 0,
                group_sales_curr={k: round(v, 2) for k, v in (c.group_sales if c else {}).items()},
                is_new=(p is None or p_sales == 0),
                is_closed=(c is None or c_sales == 0),
            )
        )
    out.sort(key=lambda s: s.real_sales_curr, reverse=True)
    return out


# ---------------------------------------------------------------------------
# 대시보드
# ---------------------------------------------------------------------------
def _build_dashboard(
    prev: ParsedFile,
    curr: ParsedFile,
    prev_aggs: dict[str, _MenuAgg],
    curr_aggs: dict[str, _MenuAgg],
    group_slices: list[GroupSlice],
) -> Dashboard:
    def totals(recs: list[MenuRecord]) -> dict[str, float]:
        return {
            "real_sales": sum(r.real_sales for r in recs),
            "order_amount": sum(r.order_amount for r in recs),
            "discount": sum(r.discount_amount for r in recs),
            "orders": sum(r.order_count for r in recs),
            "gross_profit": sum(r.gross_profit for r in recs),
        }

    ct = totals(curr.records)
    pt = totals(prev.records)

    # 분류별 매출 (그룹 태그 포함)
    cat: dict[str, list[float]] = {}
    for a in curr_aggs.values():
        cat.setdefault(a.category, [0.0, 0.0])[0] += a.real_sales
    for a in prev_aggs.values():
        cat.setdefault(a.category, [0.0, 0.0])[1] += a.real_sales
    sales_by_category = sorted(
        (
            CategorySales(
                category=k, group=group_for(k), curr=v[0], prev=v[1],
                delta_pct=_round(_pct_change(v[0], v[1])),
            )
            for k, v in cat.items()
        ),
        key=lambda c: c.curr,
        reverse=True,
    )

    return Dashboard(
        total_sales_curr=ct["real_sales"],
        total_sales_prev=pt["real_sales"],
        sales_delta_pct=_round(_pct_change(ct["real_sales"], pt["real_sales"])),
        order_count_curr=ct["orders"],
        order_count_prev=pt["orders"],
        order_delta_pct=_round(_pct_change(ct["orders"], pt["orders"])),
        profit_rate_curr=round(_safe_div(ct["gross_profit"], ct["real_sales"]) * 100.0, 2),
        profit_rate_prev=round(_safe_div(pt["gross_profit"], pt["real_sales"]) * 100.0, 2),
        discount_rate_curr=round(_safe_div(ct["discount"], ct["order_amount"]) * 100.0, 2),
        discount_rate_prev=round(_safe_div(pt["discount"], pt["order_amount"]) * 100.0, 2),
        menu_count_curr=sum(1 for a in curr_aggs.values() if not _is_unknown(a.menu_code)),
        menu_count_prev=sum(1 for a in prev_aggs.values() if not _is_unknown(a.menu_code)),
        sales_by_category=sales_by_category,
        sales_by_group=group_slices,
        monthly=[
            MonthlyPoint(label=prev.period_label, sales=pt["real_sales"], orders=pt["orders"]),
            MonthlyPoint(label=curr.period_label, sales=ct["real_sales"], orders=ct["orders"]),
        ],
    )


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------
def analyze(
    prev: ParsedFile, curr: ParsedFile, alias_map: dict[str, str] | None = None
) -> AnalysisResult:
    """전월/당월 파싱 결과를 비교 분석해 결과(AI 제외)를 반환한다.

    alias_map: {변형이름: 대표명} 수동 별칭표(선택). 유사/동의어 메뉴를 하나로 취합.
    """
    prev_menu = _aggregate_menus(prev.records, alias_map)
    curr_menu = _aggregate_menus(curr.records, alias_map)
    prev_store = _aggregate_stores(prev.records)
    curr_store = _aggregate_stores(curr.records)

    menus_full = _build_menu_analyses(prev_menu, curr_menu)
    # 이름 미상 메뉴: 순위/인사이트/메뉴표에서 제외(총매출·그룹합계엔 포함)
    ranked_menus = [m for m in menus_full if not _is_unknown(m.menu_code)]
    excluded = [m for m in menus_full if _is_unknown(m.menu_code)]

    insights = _build_insights(ranked_menus)
    total_curr_real = sum(a.real_sales for a in curr_menu.values())
    groups, group_slices = _build_group_summaries(menus_full, total_curr_real)
    stores = _build_store_analyses(prev_store, curr_store)
    dashboard = _build_dashboard(prev, curr, prev_menu, curr_menu, group_slices)

    # 이름은 없지만 분류가 있어 "기타 <분류>"로 묶어 순위·매출에 포함한 항목(투명성 안내).
    grouped = [m for m in ranked_menus if m.menu_name.startswith("기타 ")]
    notes: list[str] = []
    if grouped:
        grp_sales = sum(m.curr.real_sales for m in grouped)
        notes.append(
            f"POS에 메뉴명이 비어 출력된 항목은 분류별 '기타 OO'로 묶어 매출·순위에 포함했습니다 "
            f"(당월 {grp_sales:,.0f}원). 정확한 메뉴명은 해당 매장 POS에서 채워주세요."
        )
    if excluded:
        excl_sales = sum(m.curr.real_sales for m in excluded)
        notes.append(
            f"분류조차 없는 미상 항목은 순위에서 제외됨(당월 {excl_sales:,.0f}원). 총매출·그룹합계에는 포함."
        )
    excluded_note = " ".join(notes) if notes else None

    period_warning = _period_warning(prev, curr)
    store_count = len({r.store_code for r in curr.records})

    meta = AnalysisMeta(
        prev_label=prev.period_label,
        curr_label=curr.period_label,
        prev_period_start=prev.period_start,
        prev_period_end=prev.period_end,
        curr_period_start=curr.period_start,
        curr_period_end=curr.period_end,
        scope=curr.scope or prev.scope,
        store_count=store_count,
        generated_at=datetime.now(timezone.utc),
        excluded_note=excluded_note,
        period_warning=period_warning,
    )

    return AnalysisResult(
        meta=meta,
        dashboard=dashboard,
        insights=insights,
        groups=groups,
        menus=ranked_menus,
        stores=stores,
        ai=AIReport(),  # AI 내러티브는 상위 계층(ai 모듈)에서 채운다.
    )
