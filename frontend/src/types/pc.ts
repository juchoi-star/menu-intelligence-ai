// 백엔드 app/models/pc_schemas.py 와 1:1 대응 (피씨/PC방).

export interface PCMetrics {
  qty: number;
  sales: number;
}

export interface PCProductAnalysis {
  name: string;
  unit_price_curr: number;
  unit_price_prev: number;
  curr: PCMetrics;
  prev: PCMetrics | null;
  sales_growth_pct: number | null;
  qty_growth_pct: number | null;
  sales_delta_abs: number;
  price_change_pct: number | null;
  rank_curr: number | null;
  rank_prev: number | null;
  rank_change: number | null;
  contribution_pct: number;
  is_new: boolean;
  is_discontinued: boolean;
}

export interface PCCategorySales {
  name: string;
  curr: number;
  prev: number;
  delta_pct: number | null;
  qty_curr: number;
}

export interface PCInsightItem {
  name: string;
  value: number | null;
  curr_sales: number;
  prev_sales: number;
  detail: string;
}

export interface PCInsights {
  rising_top10: PCInsightItem[];
  falling_top10: PCInsightItem[];
  top_contributors: PCInsightItem[];
  qty_growth_top: PCInsightItem[];
  rank_up: PCInsightItem[];
  rank_down: PCInsightItem[];
  new_products: PCInsightItem[];
  discontinued_products: PCInsightItem[];
}

export interface PCMonthlyPoint {
  label: string;
  sales: number;
  qty: number;
}

export interface PCDashboard {
  total_sales_curr: number;
  total_sales_prev: number;
  sales_delta_pct: number | null;
  total_qty_curr: number;
  total_qty_prev: number;
  qty_delta_pct: number | null;
  product_count_curr: number;
  product_count_prev: number;
  avg_price_curr: number;
  sales_by_category: PCCategorySales[];
  monthly: PCMonthlyPoint[];
}

export interface PCAIReport {
  summary: string;
  product_narratives: Record<string, string>;
  recommendations: string[];
  provider: string;
}

export interface PCAnalysisMeta {
  prev_label: string;
  curr_label: string;
  output_date_prev: string | null;
  output_date_curr: string | null;
  product_count: number;
  generated_at: string;
  excluded_note: string | null;
}

export interface PCAnalysisResult {
  meta: PCAnalysisMeta;
  dashboard: PCDashboard;
  insights: PCInsights;
  categories: PCCategorySales[];
  products: PCProductAnalysis[];
  ai: PCAIReport;
}

export interface PCUploadResponse {
  analysis_id: string;
  result: PCAnalysisResult;
}
