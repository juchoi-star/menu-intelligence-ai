"""피씨(PC방) 분석 응답 스키마.

생전포차와 데이터 모델이 달라(가맹점·할인·이익 없음, 상품/분류/판매개수 중심)
별도 스키마로 분리한다. 프론트 `frontend/src/types/pc.ts` 와 대응.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PCMetrics(BaseModel):
    qty: float = 0        # 판매개수
    sales: float = 0      # 매출액


class PCProductAnalysis(BaseModel):
    name: str
    unit_price_curr: float = 0
    unit_price_prev: float = 0
    curr: PCMetrics
    prev: PCMetrics | None = None
    sales_growth_pct: float | None = None
    qty_growth_pct: float | None = None
    sales_delta_abs: float = 0
    price_change_pct: float | None = None
    rank_curr: int | None = None
    rank_prev: int | None = None
    rank_change: int | None = None
    contribution_pct: float = 0        # 당월 매출 기여도(점유율)
    is_new: bool = False
    is_discontinued: bool = False


class PCCategorySales(BaseModel):
    name: str
    curr: float = 0
    prev: float = 0
    delta_pct: float | None = None
    qty_curr: float = 0


class PCInsightItem(BaseModel):
    name: str
    value: float | None = None
    curr_sales: float = 0
    prev_sales: float = 0
    detail: str = ""


class PCInsights(BaseModel):
    rising_top10: list[PCInsightItem] = Field(default_factory=list)
    falling_top10: list[PCInsightItem] = Field(default_factory=list)
    top_contributors: list[PCInsightItem] = Field(default_factory=list)
    qty_growth_top: list[PCInsightItem] = Field(default_factory=list)
    rank_up: list[PCInsightItem] = Field(default_factory=list)
    rank_down: list[PCInsightItem] = Field(default_factory=list)
    new_products: list[PCInsightItem] = Field(default_factory=list)
    discontinued_products: list[PCInsightItem] = Field(default_factory=list)


class PCMonthlyPoint(BaseModel):
    label: str
    sales: float = 0
    qty: float = 0


class PCDashboard(BaseModel):
    total_sales_curr: float = 0
    total_sales_prev: float = 0
    sales_delta_pct: float | None = None
    total_qty_curr: float = 0
    total_qty_prev: float = 0
    qty_delta_pct: float | None = None
    product_count_curr: int = 0
    product_count_prev: int = 0
    avg_price_curr: float = 0        # 평균 객단가(매출/개수)
    sales_by_category: list[PCCategorySales] = Field(default_factory=list)
    monthly: list[PCMonthlyPoint] = Field(default_factory=list)


class PCAIReport(BaseModel):
    summary: str = ""
    product_narratives: dict[str, str] = Field(default_factory=dict)  # name -> 서술
    recommendations: list[str] = Field(default_factory=list)
    provider: str = "rule-based"


class PCAnalysisMeta(BaseModel):
    prev_label: str = "전월"
    curr_label: str = "당월"
    output_date_prev: str | None = None
    output_date_curr: str | None = None
    product_count: int = 0
    generated_at: datetime
    excluded_note: str | None = None   # 분석 제외 항목 안내(벌툰: 시간제 등 비메뉴)


class PCAnalysisResult(BaseModel):
    meta: PCAnalysisMeta
    dashboard: PCDashboard
    insights: PCInsights
    categories: list[PCCategorySales] = Field(default_factory=list)
    products: list[PCProductAnalysis] = Field(default_factory=list)
    ai: PCAIReport


class PCUploadResponse(BaseModel):
    analysis_id: str
    result: PCAnalysisResult
