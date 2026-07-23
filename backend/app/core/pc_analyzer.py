"""피씨(PC방) 상품 비교 분석 엔진.

전월/당월 두 :class:`PCParsedFile` 을 받아 상품명 기준으로 매칭하여
매출 성장률·판매개수 증감·객단가 변화·순위변화·기여도·신규/중단 상품·
분류별 증감을 계산한다. (할인·이익·가맹점 데이터는 PC POS 에 없음)
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.pc_parser import PCParsedFile
from app.models.pc_schemas import (
    PCAIReport,
    PCAnalysisMeta,
    PCAnalysisResult,
    PCCategorySales,
    PCDashboard,
    PCInsightItem,
    PCInsights,
    PCMetrics,
    PCMonthlyPoint,
    PCProductAnalysis,
)

TOP_N = 10
MIN_BASE_SALES = 1_000_000   # 상승/하락 TOP 노이즈 방지(전월 최소 매출)
MIN_QTY_BASE = 300           # 판매개수 증감 후보 최소 전월 개수
PRODUCT_LIMIT = 800          # 응답 상품표 상한(PC 는 SKU 6천+ → payload/localStorage 보호)


def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def _pct(curr: float, prev: float) -> float | None:
    if prev == 0:
        return None
    return (curr - prev) / prev * 100.0


def _round(v: float | None, n: int = 2) -> float | None:
    return round(v, n) if v is not None else None


def _rank_by_sales(products: dict[str, tuple[float, float, float]]) -> dict[str, int]:
    """매출액 내림차순 순위(1-based). products: name -> (price, qty, sales)."""
    ordered = sorted(
        ((n, v[2]) for n, v in products.items() if v[2] > 0),
        key=lambda x: x[1],
        reverse=True,
    )
    return {n: i + 1 for i, (n, _) in enumerate(ordered)}


def _as_map(pf: PCParsedFile) -> dict[str, tuple[float, float, float]]:
    """상품명 -> (단가, 개수, 매출). 동일명은 합산."""
    out: dict[str, list[float]] = {}
    for p in pf.products:
        acc = out.setdefault(p.name, [0.0, 0.0, 0.0])
        if p.unit_price:
            acc[0] = p.unit_price
        acc[1] += p.qty
        acc[2] += p.sales
    return {n: (v[0], v[1], v[2]) for n, v in out.items()}


def _to_item(p: PCProductAnalysis, value: float | None, detail: str) -> PCInsightItem:
    return PCInsightItem(
        name=p.name,
        value=_round(value),
        curr_sales=p.curr.sales,
        prev_sales=p.prev.sales if p.prev else 0.0,
        detail=detail,
    )


def _build_products(
    prev: dict[str, tuple[float, float, float]],
    curr: dict[str, tuple[float, float, float]],
) -> list[PCProductAnalysis]:
    prev_rank = _rank_by_sales(prev)
    curr_rank = _rank_by_sales(curr)
    total_curr = sum(v[2] for v in curr.values())

    out: list[PCProductAnalysis] = []
    for name in set(prev) | set(curr):
        c = curr.get(name)
        p = prev.get(name)
        c_price, c_qty, c_sales = c if c else (0.0, 0.0, 0.0)
        p_price, p_qty, p_sales = p if p else (0.0, 0.0, 0.0)

        rc, rp = curr_rank.get(name), prev_rank.get(name)
        out.append(
            PCProductAnalysis(
                name=name,
                unit_price_curr=c_price,
                unit_price_prev=p_price,
                curr=PCMetrics(qty=c_qty, sales=c_sales),
                prev=PCMetrics(qty=p_qty, sales=p_sales) if p else None,
                sales_growth_pct=_round(_pct(c_sales, p_sales)),
                qty_growth_pct=_round(_pct(c_qty, p_qty)),
                sales_delta_abs=c_sales - p_sales,
                price_change_pct=_round(_pct(c_price, p_price)) if (c_price and p_price) else None,
                rank_curr=rc,
                rank_prev=rp,
                rank_change=(rp - rc) if (rc and rp) else None,
                contribution_pct=round(_safe_div(c_sales, total_curr) * 100.0, 3),
                is_new=(p is None or p_sales == 0),
                is_discontinued=(c is None or c_sales == 0),
            )
        )
    out.sort(key=lambda x: x.curr.sales, reverse=True)
    return out


def _build_insights(products: list[PCProductAnalysis]) -> PCInsights:
    growth_pool = [
        p for p in products
        if not p.is_new and not p.is_discontinued and p.sales_growth_pct is not None
        and (p.prev.sales if p.prev else 0) >= MIN_BASE_SALES
    ]
    rising = sorted(growth_pool, key=lambda p: p.sales_growth_pct or 0, reverse=True)[:TOP_N]
    falling = sorted(growth_pool, key=lambda p: p.sales_growth_pct or 0)[:TOP_N]
    contributors = sorted(products, key=lambda p: p.curr.sales, reverse=True)[:TOP_N]

    qty_pool = [
        p for p in products
        if not p.is_new and not p.is_discontinued and p.qty_growth_pct is not None
        and (p.prev.qty if p.prev else 0) >= MIN_QTY_BASE
    ]
    qty_top = sorted(qty_pool, key=lambda p: p.qty_growth_pct or 0, reverse=True)[:TOP_N]

    rank_pool = [p for p in products if p.rank_change is not None]
    rank_up = sorted((p for p in rank_pool if (p.rank_change or 0) > 0),
                     key=lambda p: p.rank_change or 0, reverse=True)[:TOP_N]
    rank_down = sorted((p for p in rank_pool if (p.rank_change or 0) < 0),
                       key=lambda p: p.rank_change or 0)[:TOP_N]

    new_products = sorted((p for p in products if p.is_new and p.curr.sales > 0),
                          key=lambda p: p.curr.sales, reverse=True)[:TOP_N]
    discontinued = sorted(
        (p for p in products if p.is_discontinued and p.prev and p.prev.sales >= MIN_BASE_SALES),
        key=lambda p: p.prev.sales if p.prev else 0, reverse=True)[:TOP_N]

    return PCInsights(
        rising_top10=[_to_item(p, p.sales_growth_pct, f"매출 {p.sales_growth_pct}% ↑") for p in rising],
        falling_top10=[_to_item(p, p.sales_growth_pct, f"매출 {p.sales_growth_pct}% ↓") for p in falling],
        top_contributors=[_to_item(p, p.contribution_pct, f"점유 {p.contribution_pct}%") for p in contributors],
        qty_growth_top=[_to_item(p, p.qty_growth_pct, f"판매 {p.qty_growth_pct}% ↑") for p in qty_top],
        rank_up=[_to_item(p, p.rank_change, f"{p.rank_prev}위 → {p.rank_curr}위") for p in rank_up],
        rank_down=[_to_item(p, p.rank_change, f"{p.rank_prev}위 → {p.rank_curr}위") for p in rank_down],
        new_products=[_to_item(p, p.curr.sales, "신규 진입") for p in new_products],
        discontinued_products=[_to_item(p, p.prev.sales if p.prev else 0, "판매 중단") for p in discontinued],
    )


def _build_categories(prev: PCParsedFile, curr: PCParsedFile) -> list[PCCategorySales]:
    pmap = {c.name: c for c in prev.categories}
    cmap = {c.name: c for c in curr.categories}
    out: list[PCCategorySales] = []
    for name in set(pmap) | set(cmap):
        c = cmap.get(name)
        p = pmap.get(name)
        c_sales = c.sales if c else 0.0
        p_sales = p.sales if p else 0.0
        out.append(
            PCCategorySales(
                name=name, curr=c_sales, prev=p_sales,
                delta_pct=_round(_pct(c_sales, p_sales)),
                qty_curr=c.qty if c else 0.0,
            )
        )
    out.sort(key=lambda x: x.curr, reverse=True)
    return out


def analyze_pc(
    prev: PCParsedFile,
    curr: PCParsedFile,
    prev_label: str = "전월",
    curr_label: str = "당월",
) -> PCAnalysisResult:
    prev_map = _as_map(prev)
    curr_map = _as_map(curr)
    products = _build_products(prev_map, curr_map)
    insights = _build_insights(products)  # 전체 상품 기준으로 계산
    categories = _build_categories(prev, curr)
    # 응답 상품표는 상위 매출 기준으로 제한(집계/인사이트는 전체 사용).
    products_view = sorted(
        products, key=lambda p: max(p.curr.sales, p.prev.sales if p.prev else 0), reverse=True
    )[:PRODUCT_LIMIT]

    tot_c = sum(v[2] for v in curr_map.values())
    tot_p = sum(v[2] for v in prev_map.values())
    qty_c = sum(v[1] for v in curr_map.values())
    qty_p = sum(v[1] for v in prev_map.values())

    dashboard = PCDashboard(
        total_sales_curr=tot_c,
        total_sales_prev=tot_p,
        sales_delta_pct=_round(_pct(tot_c, tot_p)),
        total_qty_curr=qty_c,
        total_qty_prev=qty_p,
        qty_delta_pct=_round(_pct(qty_c, qty_p)),
        product_count_curr=sum(1 for v in curr_map.values() if v[2] > 0),
        product_count_prev=sum(1 for v in prev_map.values() if v[2] > 0),
        avg_price_curr=round(_safe_div(tot_c, qty_c), 0),
        sales_by_category=categories[:12],
        monthly=[
            PCMonthlyPoint(label=prev_label, sales=tot_p, qty=qty_p),
            PCMonthlyPoint(label=curr_label, sales=tot_c, qty=qty_c),
        ],
    )

    meta = PCAnalysisMeta(
        prev_label=prev_label,
        curr_label=curr_label,
        output_date_prev=prev.output_date,
        output_date_curr=curr.output_date,
        product_count=len(products),
        generated_at=datetime.now(timezone.utc),
    )

    return PCAnalysisResult(
        meta=meta,
        dashboard=dashboard,
        insights=insights,
        categories=categories,
        products=products_view,
        ai=PCAIReport(),
    )
