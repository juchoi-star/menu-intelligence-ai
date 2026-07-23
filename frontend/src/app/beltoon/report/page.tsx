"use client";

import { useBeltoonAnalysis } from "@/lib/beltoonStore";
import { BeltoonTopbar } from "@/components/beltoon/BeltoonTopbar";
import { EmptyState } from "@/components/EmptyState";
import { Card, CardBody, SectionHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { won, num } from "@/lib/format";

export default function BeltoonReportPage() {
  const { result, hydrated } = useBeltoonAnalysis();

  if (!hydrated) return <><BeltoonTopbar title="AI Report" /></>;
  if (!result)
    return (
      <>
        <BeltoonTopbar title="AI Report" />
        <EmptyState description="벌툰 대시보드에서 월별 파일들을 업로드해 분석을 실행하세요." />
      </>
    );

  const d = result.dashboard;

  return (
    <>
      <BeltoonTopbar title="AI Report" />
      <div className="mx-auto max-w-3xl space-y-6">
        <Card>
          <CardBody>
            <SectionHeader title="1. 매출 요약" subtitle={`${result.meta.prev_label} → ${result.meta.curr_label}`} />
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Tile label="총매출" value={won(d.total_sales_curr)} />
              <Tile label="판매개수" value={num(d.total_qty_curr)} />
              <Tile label="평균 객단가" value={won(d.avg_price_curr)} />
              <Tile label="판매 상품수" value={num(d.product_count_curr)} />
            </div>
            <p className="mt-4 text-[15px] leading-relaxed text-white/85">{result.ai.summary}</p>
          </CardBody>
        </Card>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <ListCard title="2. 상품 성장 (상승 TOP10)" items={result.insights.rising_top10} tone="pos" />
          <ListCard title="3. 상품 감소 (하락 TOP10)" items={result.insights.falling_top10} tone="neg" />
        </div>

        <Card>
          <CardBody>
            <SectionHeader title="4. 분류별 매출" />
            <div className="space-y-2">
              {result.categories.slice(0, 8).map((c) => (
                <div key={c.name} className="flex items-center justify-between border-b border-line/40 pb-2 text-sm last:border-0">
                  <span className="text-white/85">{c.name}</span>
                  <span className="text-muted">{won(c.curr)} · {c.delta_pct == null ? "신규" : `${c.delta_pct}%`}</span>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <SectionHeader title="5. AI 분석" subtitle={`제공자: ${result.ai.provider}`} />
            <div className="space-y-3">
              {Object.entries(result.ai.product_narratives).map(([name, text]) => (
                <div key={name} className="rounded-xl border border-line/60 bg-ink-800/40 p-3.5">
                  <div className="mb-1 text-sm font-semibold text-accent">{name}</div>
                  <p className="text-sm leading-relaxed text-white/80">{text}</p>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        <Card className="shadow-glow">
          <CardBody>
            <SectionHeader title="6. 추천 액션" />
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
    </>
  );
}

function Tile({ label, value }: { label: string; value: string }) {
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
  items: { name: string; detail: string }[];
  tone: "pos" | "neg";
}) {
  return (
    <Card>
      <CardBody>
        <SectionHeader title={title} />
        <div className="space-y-1.5">
          {items.length === 0 && <div className="text-sm text-muted">해당 없음</div>}
          {items.map((it) => (
            <div key={it.name} className="flex items-center justify-between gap-2 text-sm">
              <span className="min-w-0 truncate text-white/85">{it.name}</span>
              <Badge tone={tone}>{it.detail}</Badge>
            </div>
          ))}
        </div>
      </CardBody>
    </Card>
  );
}
