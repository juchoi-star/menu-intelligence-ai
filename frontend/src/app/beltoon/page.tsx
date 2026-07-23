"use client";

import Link from "next/link";
import { useBeltoonAnalysis } from "@/lib/beltoonStore";
import { BeltoonTopbar } from "@/components/beltoon/BeltoonTopbar";
import { BeltoonUploadPanel } from "@/components/beltoon/BeltoonUploadPanel";
import { PCInsightList } from "@/components/pc/PCInsightList";
import { PCCategoryChart } from "@/components/pc/PCCategoryChart";
import { StatCard } from "@/components/StatCard";
import { Card, CardBody, SectionHeader } from "@/components/ui/Card";
import { won, wonShort, num, pct } from "@/lib/format";

export default function BeltoonDashboard() {
  const { result, hydrated } = useBeltoonAnalysis();

  return (
    <>
      <BeltoonTopbar title="Dashboard" />
      <div className="space-y-6">
        <BeltoonUploadPanel />

        {!hydrated ? null : !result ? (
          <Card>
            <CardBody className="py-12 text-center text-muted">
              분석을 실행하면 상품 매출 요약과 인사이트가 여기에 표시됩니다.
            </CardBody>
          </Card>
        ) : (
          <>
            {result.meta.excluded_note && (
              <div className="flex items-start gap-2.5 rounded-xl border border-line/70 bg-ink-800/40 px-4 py-3 text-sm text-muted">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" className="mt-0.5 h-4 w-4 shrink-0 text-gold">
                  <path d="M12 9v4m0 4h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <span>{result.meta.excluded_note}</span>
              </div>
            )}
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
              <StatCard accent label="총매출" value={won(result.dashboard.total_sales_curr)}
                delta={result.dashboard.sales_delta_pct} hint={`전월 ${wonShort(result.dashboard.total_sales_prev)}`} />
              <StatCard label="전월 대비" value={pct(result.dashboard.sales_delta_pct)}
                hint={`${wonShort(result.dashboard.total_sales_curr - result.dashboard.total_sales_prev)} 변동`} />
              <StatCard label="판매개수" value={num(result.dashboard.total_qty_curr)}
                delta={result.dashboard.qty_delta_pct} hint={`전월 ${num(result.dashboard.total_qty_prev)}`} />
              <StatCard label="평균 객단가" value={won(result.dashboard.avg_price_curr)} hint="매출 ÷ 판매개수" />
              <StatCard label="판매 상품수" value={num(result.dashboard.product_count_curr)}
                hint={`전월 ${num(result.dashboard.product_count_prev)}`} />
            </div>

            <Card>
              <CardBody>
                <SectionHeader title="분류별 매출" subtitle="당월 vs 전월 (상위 12)" />
                <PCCategoryChart data={result.dashboard.sales_by_category} />
              </CardBody>
            </Card>

            <Card className="shadow-glow">
              <CardBody>
                <SectionHeader title="AI 분석 요약" subtitle={`제공자: ${result.ai.provider}`}
                  right={<Link href="/beltoon/report" className="text-sm font-medium text-accent hover:underline">전체 리포트 →</Link>} />
                <p className="text-[15px] leading-relaxed text-white/85">{result.ai.summary}</p>
              </CardBody>
            </Card>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <PCInsightList title="매출 상승 TOP10" items={result.insights.rising_top10} tone="pos" />
              <PCInsightList title="매출 하락 TOP10" items={result.insights.falling_top10} tone="neg" />
            </div>
          </>
        )}
      </div>
    </>
  );
}
