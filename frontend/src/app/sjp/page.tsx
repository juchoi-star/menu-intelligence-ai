"use client";

import Link from "next/link";
import { useAnalysis } from "@/lib/store";
import { Topbar } from "@/components/layout/Topbar";
import { UploadPanel } from "@/components/UploadPanel";
import { StatCard } from "@/components/StatCard";
import { InsightList } from "@/components/InsightList";
import { GroupBreakdown } from "@/components/GroupBreakdown";
import { Card, CardBody, SectionHeader } from "@/components/ui/Card";
import { CategoryBarChart } from "@/components/charts/Charts";
import { won, wonShort, num, pct } from "@/lib/format";

const RANK_TONE: Record<string, "gold" | "neutral" | "accent" | "pos"> = {
  주류: "gold",
  막걸리: "neutral",
  음식: "accent",
};

export default function DashboardPage() {
  const { result, hydrated } = useAnalysis();

  return (
    <>
      <Topbar title="Dashboard" />
      <div className="space-y-6">
        <UploadPanel />

        {!hydrated ? null : !result ? (
          <Card>
            <CardBody className="py-12 text-center text-muted">
              분석을 실행하면 이번 달 매출 요약과 인사이트가 여기에 표시됩니다.
            </CardBody>
          </Card>
        ) : (
          <>
            {result.meta.period_warning && (
              <div className="flex items-start gap-2.5 rounded-xl border border-neg/40 bg-neg/10 px-4 py-3 text-sm text-neg">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="mt-0.5 h-5 w-5 shrink-0">
                  <path d="M12 9v4m0 4h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <span className="font-medium">{result.meta.period_warning}</span>
              </div>
            )}

            {/* KPI 카드 */}
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
              <StatCard
                accent
                label="이번달 총매출"
                value={won(result.dashboard.total_sales_curr)}
                delta={result.dashboard.sales_delta_pct}
                hint={`전월 ${wonShort(result.dashboard.total_sales_prev)}`}
              />
              <StatCard
                label="전월 대비"
                value={pct(result.dashboard.sales_delta_pct)}
                hint={`${wonShort(result.dashboard.total_sales_curr - result.dashboard.total_sales_prev)} 변동`}
              />
              <StatCard
                label="주문건수"
                value={num(result.dashboard.order_count_curr)}
                delta={result.dashboard.order_delta_pct}
                hint={`전월 ${num(result.dashboard.order_count_prev)}`}
              />
              <StatCard
                label="이익률"
                value={`${result.dashboard.profit_rate_curr}%`}
                hint={`할인율 ${result.dashboard.discount_rate_curr}%`}
              />
              <StatCard
                label="판매 메뉴수"
                value={num(result.dashboard.menu_count_curr)}
                hint={`전월 ${num(result.dashboard.menu_count_prev)}`}
              />
            </div>

            {result.meta.excluded_note && (
              <div className="flex items-start gap-2.5 rounded-xl border border-line/70 bg-ink-800/40 px-4 py-3 text-sm text-muted">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" className="mt-0.5 h-4 w-4 shrink-0 text-gold">
                  <path d="M12 9v4m0 4h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <span>{result.meta.excluded_note}</span>
              </div>
            )}

            {/* 그룹별(주류/막걸리/음식/기타) 분해 */}
            <GroupBreakdown groups={result.dashboard.sales_by_group} />

            {/* 분류별 매출 */}
            <Card>
              <CardBody>
                <SectionHeader title="분류별 매출" subtitle="당월 vs 전월 실매출" />
                <CategoryBarChart data={result.dashboard.sales_by_category} />
              </CardBody>
            </Card>

            {/* 그룹별 매출 순위 (주류·막걸리·음식 분리 — 술이 음식 순위에 섞이지 않게) */}
            <div>
              <SectionHeader
                title="그룹별 매출 순위"
                subtitle="주류·막걸리·음식을 나눠 표시 (그룹 내 당월 실매출 기준)"
              />
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
                {result.groups
                  .filter((g) => g.group !== "기타")
                  .map((g) => (
                    <InsightList
                      key={g.group}
                      title={`${g.group} TOP`}
                      items={g.insights.top_contributors}
                      tone={RANK_TONE[g.group] ?? "neutral"}
                    />
                  ))}
              </div>
            </div>

            {/* AI 요약 */}
            <Card className="shadow-glow">
              <CardBody>
                <SectionHeader
                  title="AI 분석 요약"
                  subtitle={`제공자: ${result.ai.provider}`}
                  right={
                    <Link href="/sjp/report" className="text-sm font-medium text-accent hover:underline">
                      전체 리포트 →
                    </Link>
                  }
                />
                <p className="text-[15px] leading-relaxed text-white/85">{result.ai.summary}</p>
              </CardBody>
            </Card>

            {/* 상승/하락 미리보기 */}
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <InsightList title="상승 TOP10" items={result.insights.rising_top10} tone="pos" />
              <InsightList title="하락 TOP10" items={result.insights.falling_top10} tone="neg" />
            </div>
          </>
        )}
      </div>
    </>
  );
}
