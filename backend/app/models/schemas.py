"""API 응답 Pydantic 스키마.

프론트엔드 TypeScript 타입(`frontend/src/types/index.ts`)과 1:1로 대응한다.
분석 엔진(:mod:`app.core.analyzer`)이 이 모델들을 직접 구성해 반환한다.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class PeriodMetrics(BaseModel):
    """한 달치 메뉴/가맹점 집계 지표."""

    order_count: float = 0
    order_amount: float = 0
    discount_amount: float = 0
    real_sales: float = 0
    net_sales: float = 0
    cogs: float = 0
    gross_profit: float = 0
    store_count: int = 0


class StoreDelta(BaseModel):
    """메뉴 상세의 가맹점별 증감 행."""

    store_code: str
    store_name: str
    curr_real_sales: float = 0
    prev_real_sales: float = 0
    sales_delta_pct: float | None = None
    curr_orders: float = 0
    prev_orders: float = 0
    orders_delta_pct: float | None = None


class MenuAnalysis(BaseModel):
    """체인 전체로 합산한 메뉴 단위 분석 결과."""

    menu_code: str
    menu_name: str
    category: str
    group: str = "기타"                          # 상위 그룹(주류/음식/기타)

    curr: PeriodMetrics
    prev: PeriodMetrics | None = None

    unit_price: float = 0

    sales_growth_pct: float | None = None      # 실매출 성장률(%)
    order_growth_pct: float | None = None       # 주문건수 증감률(%)
    sales_delta_abs: float = 0                   # 실매출 절대 증감액

    discount_rate_curr: float = 0                # 할인율(%) = 할인/주문금액
    discount_rate_prev: float = 0
    discount_rate_delta: float = 0

    profit_rate_curr: float = 0                  # 이익률(%) = 매출이익/실매출
    profit_rate_prev: float = 0

    rank_curr: int | None = None                 # 그룹 내 실매출 기준 순위
    rank_prev: int | None = None
    rank_change: int | None = None               # +면 상승

    contribution_pct: float = 0                  # 그룹 내 당월 실매출 기여도(%)
    contribution_overall_pct: float = 0          # 전체 대비 당월 실매출 기여도(%)

    is_new: bool = False                         # 신규 메뉴
    is_discontinued: bool = False                # 판매중단 메뉴
    grew_without_discount: bool = False          # 할인 없이 성장

    by_store: list[StoreDelta] = Field(default_factory=list)


class StoreAnalysis(BaseModel):
    """가맹점 단위 분석 결과."""

    store_code: str
    store_name: str
    real_sales_curr: float = 0
    real_sales_prev: float = 0
    sales_delta_pct: float | None = None
    order_count_curr: float = 0
    order_count_prev: float = 0
    order_delta_pct: float | None = None
    gross_profit_curr: float = 0
    profit_rate_curr: float = 0
    discount_rate_curr: float = 0
    menu_count_curr: int = 0
    group_sales_curr: dict[str, float] = Field(default_factory=dict)  # 그룹별 당월 실매출


class CategorySales(BaseModel):
    category: str
    group: str = "기타"
    curr: float = 0
    prev: float = 0
    delta_pct: float | None = None


class GroupSlice(BaseModel):
    """대시보드 그룹별(주류/음식/기타) 요약 지표."""

    group: str
    real_sales_curr: float = 0
    real_sales_prev: float = 0
    sales_delta_pct: float | None = None
    order_count_curr: float = 0
    order_count_prev: float = 0
    order_delta_pct: float | None = None
    profit_rate_curr: float = 0
    discount_rate_curr: float = 0
    discount_rate_prev: float = 0
    menu_count_curr: int = 0
    contribution_pct: float = 0                  # 전체 실매출 대비 비중


class MonthlyPoint(BaseModel):
    label: str
    sales: float = 0
    orders: float = 0


class Dashboard(BaseModel):
    """첫 화면 카드 + 요약 차트 데이터."""

    total_sales_curr: float = 0
    total_sales_prev: float = 0
    sales_delta_pct: float | None = None
    order_count_curr: float = 0
    order_count_prev: float = 0
    order_delta_pct: float | None = None
    profit_rate_curr: float = 0
    profit_rate_prev: float = 0
    discount_rate_curr: float = 0
    discount_rate_prev: float = 0
    menu_count_curr: int = 0
    menu_count_prev: int = 0
    sales_by_category: list[CategorySales] = Field(default_factory=list)
    sales_by_group: list[GroupSlice] = Field(default_factory=list)
    monthly: list[MonthlyPoint] = Field(default_factory=list)


class MenuInsightItem(BaseModel):
    """인사이트 리스트(상승/하락/순위 등)용 경량 아이템."""

    menu_code: str
    menu_name: str
    category: str
    value: float | None = None          # 대표 수치(성장률/기여도/순위변화 등)
    curr_real_sales: float = 0
    prev_real_sales: float = 0
    detail: str = ""                     # 표기용 보조 설명


class Insights(BaseModel):
    rising_top10: list[MenuInsightItem] = Field(default_factory=list)
    falling_top10: list[MenuInsightItem] = Field(default_factory=list)
    top_contributors: list[MenuInsightItem] = Field(default_factory=list)
    order_growth_top: list[MenuInsightItem] = Field(default_factory=list)
    rank_up: list[MenuInsightItem] = Field(default_factory=list)
    rank_down: list[MenuInsightItem] = Field(default_factory=list)
    new_menus: list[MenuInsightItem] = Field(default_factory=list)
    discontinued_menus: list[MenuInsightItem] = Field(default_factory=list)
    grew_without_discount: list[MenuInsightItem] = Field(default_factory=list)


class GroupSummary(BaseModel):
    """그룹(주류/음식/기타) 단위 분석 묶음 — 메뉴 분석 탭에서 사용."""

    group: str
    metrics: GroupSlice
    sales_by_category: list[CategorySales] = Field(default_factory=list)
    insights: "Insights"


class AIReport(BaseModel):
    """AI 분석 내러티브."""

    summary: str = ""                                # 매출 요약 스토리
    menu_narratives: dict[str, str] = Field(default_factory=dict)  # menu_code -> 서술
    recommendations: list[str] = Field(default_factory=list)       # 추천 액션
    provider: str = "rule-based"                     # 'openai' | 'rule-based'


class AnalysisMeta(BaseModel):
    prev_label: str
    curr_label: str
    prev_period_start: date | None = None
    prev_period_end: date | None = None
    curr_period_start: date | None = None
    curr_period_end: date | None = None
    scope: str | None = None
    store_count: int = 0
    generated_at: datetime
    excluded_note: str | None = None   # 순위 제외 안내(이름 미상 메뉴)


class AnalysisResult(BaseModel):
    """업로드 → 비교 분석의 최종 응답."""

    meta: AnalysisMeta
    dashboard: Dashboard
    insights: Insights                                  # 전체(전 그룹 통합) 인사이트
    groups: list[GroupSummary] = Field(default_factory=list)  # 그룹별 분석(주류/음식/기타)
    menus: list[MenuAnalysis] = Field(default_factory=list)
    stores: list[StoreAnalysis] = Field(default_factory=list)
    ai: AIReport


class UploadResponse(BaseModel):
    """분석 저장 후 반환(조회용 id 포함)."""

    analysis_id: str
    result: AnalysisResult
