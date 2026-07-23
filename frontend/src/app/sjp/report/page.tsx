"use client";

import { useAnalysis } from "@/lib/store";
import { Topbar } from "@/components/layout/Topbar";
import { EmptyState } from "@/components/EmptyState";
import { Card, CardBody, SectionHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { GroupBreakdown } from "@/components/GroupBreakdown";
import { reportPdfUrl } from "@/lib/api";
import { won, num } from "@/lib/format";

const TOC = [
  "매출 요약",
  "메뉴 성장",
  "메뉴 감소",
  "순위 변화",
  "가맹점 분석",
  "AI 분석",
  "추천 액션",
];

export default function ReportPage() {
  const { result, analysisId, hydrated } = useAnalysis();

  if (!hydrated) return <><Topbar title="AI Report" /></>;
  if (!result)
    return (
      <>
        <Topbar title="AI Report" />
        <EmptyState />
      </>
    );

  const d = result.dashboard;
  const byCode = new Map(result.menus.map((m) => [m.menu_code, m]));

  return (
    <>
      <Topbar title="AI Report" />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[220px_1fr]">
        {/* 목차 */}
        <aside className="lg:sticky lg:top-24 lg:self-start">
          <Card>
            <CardBody>
              <div className="stat-label mb-3">목차</div>
              <ol className="space-y-1.5 text-sm">
                {TOC.map((t, i) => (
                  <li key={t} className="flex items-center gap-2 text-white/80">
                    <span className="grid h-5 w-5 place-items-center rounded bg-white/[0.06] text-[11px] text-muted">
                      {i + 1}
                    </span>
                    {t}
                  </li>
                ))}
              </ol>
              {analysisId && (
                <a
                  href={reportPdfUrl(analysisId)}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-accent px-4 py-2.5 text-sm font-semibold text-ink-950 hover:bg-accent-soft"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-4 w-4">
                    <path d="M12 3v12m0 0 4-4m-4 4-4-4M5 21h14" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  PDF 보고서 다운로드
                </a>
              )}
            </CardBody>
          </Card>
        </aside>

        <div className="space-y-6">
          {/* 1. 매출 요약 */}
          <Card>
            <CardBody>
              <SectionHeader title="1. 매출 요약" />
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <SummaryTile label="실매출" value={won(d.total_sales_curr)} />
                <SummaryTile label="주문건수" value={num(d.order_count_curr)} />
                <SummaryTile label="이익률" value={`${d.profit_rate_curr}%`} />
                <SummaryTile label="할인율" value={`${d.discount_rate_curr}%`} />
              </div>
              <p className="mt-4 text-[15px] leading-relaxed text-white/85">{result.ai.summary}</p>
            </CardBody>
          </Card>

          {/* 그룹별 분해 */}
          <GroupBreakdown groups={result.dashboard.sales_by_group} />

          {/* 2~3. 성장/감소 */}
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <ListCard title="2. 메뉴 성장" items={result.insights.rising_top10} tone="pos" />
            <ListCard title="3. 메뉴 감소" items={result.insights.falling_top10} tone="neg" />
          </div>

          {/* 4. 순위 변화 */}
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <ListCard title="4-1. 순위 상승" items={result.insights.rank_up} tone="pos" />
            <ListCard title="4-2. 순위 하락" items={result.insights.rank_down} tone="neg" />
          </div>

          {/* 5. 가맹점 분석 */}
          <Card>
            <CardBody>
              <SectionHeader title="5. 가맹점 분석" subtitle="당월 실매출 상위" />
              <div className="space-y-2">
                {result.stores.slice(0, 8).map((s) => (
                  <div key={s.store_code} className="flex items-center justify-between border-b border-line/40 pb-2 text-sm last:border-0">
                    <span className="text-white/85">{s.store_name}</span>
                    <span className="text-muted">
                      {won(s.real_sales_curr)} · 이익률 {s.profit_rate_curr}%
                    </span>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>

          {/* 6. AI 분석 */}
          <Card>
            <CardBody>
              <SectionHeader title="6. AI 분석" subtitle={`제공자: ${result.ai.provider}`} />
              <div className="space-y-3">
                {Object.entries(result.ai.menu_narratives).map(([code, text]) => (
                  <div key={code} className="rounded-xl border border-line/60 bg-ink-800/40 p-3.5">
                    <div className="mb-1 text-sm font-semibold text-accent">
                      {byCode.get(code)?.menu_name ?? code}
                    </div>
                    <p className="text-sm leading-relaxed text-white/80">{text}</p>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>

          {/* 7. 추천 액션 */}
          <Card className="shadow-glow">
            <CardBody>
              <SectionHeader title="7. 추천 액션" />
              <ul className="space-y-2.5">
                {result.ai.recommendations.map((r, i) => (
                  <li key={i} className="flex gap-3 text-[15px] text-white/85">
                    <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full bg-accent/15 text-xs font-bold text-accent">
                      {i + 1}
                    </span>
                    {r}
                  </li>
                ))}
              </ul>
            </CardBody>
          </Card>
        </div>
      </div>
    </>
  );
}

function SummaryTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-line/60 bg-ink-800/40 p-3">
      <div className="stat-label">{label}</div>
      <div className="mt-1 text-lg font-semibold text-white">{value}</div>
    </div>
  );
}

function ListCard({
  title,
  items,
  tone,
}: {
  title: string;
  items: { menu_code: string; menu_name: string; detail: string }[];
  tone: "pos" | "neg";
}) {
  return (
    <Card>
      <CardBody>
        <SectionHeader title={title} />
        <div className="space-y-1.5">
          {items.length === 0 && <div className="text-sm text-muted">해당 없음</div>}
          {items.map((it) => (
            <div key={it.menu_code} className="flex items-center justify-between text-sm">
              <span className="text-white/85">{it.menu_name}</span>
              <Badge tone={tone}>{it.detail}</Badge>
            </div>
          ))}
        </div>
      </CardBody>
    </Card>
  );
}
