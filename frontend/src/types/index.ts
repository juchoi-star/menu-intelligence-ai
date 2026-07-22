// 백엔드 app/models/schemas.py 와 1:1 대응하는 타입 정의.

export interface PeriodMetrics {
  order_count: number;
  order_amount: number;
  discount_amount: number;
  real_sales: number;
  net_sales: number;
  cogs: number;
  gross_profit: number;
  store_count: number;
}

export interface StoreDelta {
  store_code: string;
  store_name: string;
  curr_real_sales: number;
  prev_real_sales: number;
  sales_delta_pct: number | null;
  curr_orders: number;
  prev_orders: number;
  orders_delta_pct: number | null;
}

export interface MenuAnalysis {
  menu_code: string;
  menu_name: string;
  category: string;
  group: string;
  curr: PeriodMetrics;
  prev: PeriodMetrics | null;
  unit_price: number;
  sales_growth_pct: number | null;
  order_growth_pct: number | null;
  sales_delta_abs: number;
  discount_rate_curr: number;
  discount_rate_prev: number;
  discount_rate_delta: number;
  profit_rate_curr: number;
  profit_rate_prev: number;
  rank_curr: number | null;
  rank_prev: number | null;
  rank_change: number | null;
  contribution_pct: number;
  contribution_overall_pct: number;
  is_new: boolean;
  is_discontinued: boolean;
  grew_without_discount: boolean;
  by_store: StoreDelta[];
}

export interface StoreAnalysis {
  store_code: string;
  store_name: string;
  real_sales_curr: number;
  real_sales_prev: number;
  sales_delta_pct: number | null;
  order_count_curr: number;
  order_count_prev: number;
  order_delta_pct: number | null;
  gross_profit_curr: number;
  profit_rate_curr: number;
  discount_rate_curr: number;
  menu_count_curr: number;
  group_sales_curr: Record<string, number>;
}

export interface CategorySales {
  category: string;
  group: string;
  curr: number;
  prev: number;
  delta_pct: number | null;
}

export interface GroupSlice {
  group: string;
  real_sales_curr: number;
  real_sales_prev: number;
  sales_delta_pct: number | null;
  order_count_curr: number;
  order_count_prev: number;
  order_delta_pct: number | null;
  profit_rate_curr: number;
  discount_rate_curr: number;
  discount_rate_prev: number;
  menu_count_curr: number;
  contribution_pct: number;
}

export interface MonthlyPoint {
  label: string;
  sales: number;
  orders: number;
}

export interface Dashboard {
  total_sales_curr: number;
  total_sales_prev: number;
  sales_delta_pct: number | null;
  order_count_curr: number;
  order_count_prev: number;
  order_delta_pct: number | null;
  profit_rate_curr: number;
  profit_rate_prev: number;
  discount_rate_curr: number;
  discount_rate_prev: number;
  menu_count_curr: number;
  menu_count_prev: number;
  sales_by_category: CategorySales[];
  sales_by_group: GroupSlice[];
  monthly: MonthlyPoint[];
}

export interface MenuInsightItem {
  menu_code: string;
  menu_name: string;
  category: string;
  value: number | null;
  curr_real_sales: number;
  prev_real_sales: number;
  detail: string;
}

export interface Insights {
  rising_top10: MenuInsightItem[];
  falling_top10: MenuInsightItem[];
  top_contributors: MenuInsightItem[];
  order_growth_top: MenuInsightItem[];
  rank_up: MenuInsightItem[];
  rank_down: MenuInsightItem[];
  new_menus: MenuInsightItem[];
  discontinued_menus: MenuInsightItem[];
  grew_without_discount: MenuInsightItem[];
}

export interface GroupSummary {
  group: string;
  metrics: GroupSlice;
  sales_by_category: CategorySales[];
  insights: Insights;
}

export interface AIReport {
  summary: string;
  menu_narratives: Record<string, string>;
  recommendations: string[];
  provider: string;
}

export interface AnalysisMeta {
  prev_label: string;
  curr_label: string;
  prev_period_start: string | null;
  prev_period_end: string | null;
  curr_period_start: string | null;
  curr_period_end: string | null;
  scope: string | null;
  store_count: number;
  generated_at: string;
}

export interface AnalysisResult {
  meta: AnalysisMeta;
  dashboard: Dashboard;
  insights: Insights;
  groups: GroupSummary[];
  menus: MenuAnalysis[];
  stores: StoreAnalysis[];
  ai: AIReport;
}

export interface UploadResponse {
  analysis_id: string;
  result: AnalysisResult;
}
