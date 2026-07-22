"use client";

import { useParams, useRouter } from "next/navigation";
import { useAnalysis } from "@/lib/store";
import { Topbar } from "@/components/layout/Topbar";
import { EmptyState } from "@/components/EmptyState";
import { Card, CardBody, SectionHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { won, num, pct, deltaClass } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { MenuAnalysis, PeriodMetrics } from "@/types";

function MetricRow({
  label,
  curr,
  prev,
  fmt,
  delta,
}: {
  label: string;
  curr: string;
  prev: string;
  fmt?: string;
  delta?: number | null;
}) {
  return (
    <div className="flex items-center justify-between border-b border-line/50 py-3 last:border-0">
      <span className="text-sm text-muted">{label}</span>
      <div className="flex items-baseline gap-3">
        <span className="text-xs text-muted/70">전월 {prev}</span>
        <span className="text-base font-semibold text-white">{curr}{fmt}</span>
        {delta != null && (
          <span className={cn("w-16 text-right text-sm font-medium", deltaClass(delta))}>
            {pct(delta)}
          </span>
        )}
      </div>
    </div>
  );
}

export default function MenuDetailPage() {
  const params = useParams<{ code: string }>();
  const router = useRouter();
  const { result, hydrated } = useAnalysis();
  const code = decodeURIComponent(params.code);

  if (!hydrated) return <><Topbar title="메뉴 상세" /></>;
  if (!result)
    return (
      <>
        <Topbar title="메뉴 상세" />
        <EmptyState />
      </>
    );

  const menu = result.menus.find((m) => m.menu_code === code) as MenuAnalysis | undefined;
  if (!menu)
    return (
      <>
        <Topbar title="메뉴 상세" />
        <EmptyState title="메뉴를 찾을 수 없습니다" description="목록에서 다시 선택해 주세요." showCta={false} />
      </>
    );

  const c = menu.curr;
  const p: PeriodMetrics | null = menu.prev;
  const narrative = result.ai.menu_narratives[menu.menu_code];

  return (
    <>
      <Topbar title="메뉴 상세" />
      <div className="space-y-6">
        <button
          onClick={() => router.back()}
          className="text-sm text-muted transition-colors hover:text-white"
        >
          ← 돌아가기
        </button>

        {/* 헤더 */}
        <Card>
          <CardBody className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-2xl font-semibold text-white">{menu.menu_name}</h2>
                {menu.is_new && <Badge tone="accent">신규</Badge>}
                {menu.is_discontinued && <Badge tone="neg">판매중단</Badge>}
                {menu.grew_without_discount && <Badge tone="gold">할인없이 성장</Badge>}
              </div>
              <div className="mt-1 flex items-center gap-2 text-sm text-muted">
                <Badge tone="neutral">{menu.group}</Badge>
                {menu.category} · 코드 {menu.menu_code} · 단가 {won(menu.unit_price)}
              </div>
            </div>
            <div className="flex gap-6">
              <div className="text-right">
                <div className="stat-label">{menu.group} 내 순위</div>
                <div className="text-2xl font-semibold text-white">
                  {menu.rank_curr ?? "–"}
                  {menu.rank_change != null && menu.rank_change !== 0 && (
                    <span className={cn("ml-1 text-sm", menu.rank_change > 0 ? "text-pos" : "text-neg")}>
                      {menu.rank_change > 0 ? `▲${menu.rank_change}` : `▼${Math.abs(menu.rank_change)}`}
                    </span>
                  )}
                </div>
              </div>
              <div className="text-right">
                <div className="stat-label">그룹 내 기여도</div>
                <div className="text-2xl font-semibold text-white">{menu.contribution_pct}%</div>
                <div className="mt-0.5 text-[11px] text-muted">전체 {menu.contribution_overall_pct}%</div>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* AI 내러티브 */}
        {narrative && (
          <Card className="shadow-glow">
            <CardBody>
              <div className="mb-2 flex items-center gap-2">
                <Badge tone="accent">AI 분석</Badge>
              </div>
              <p className="text-[15px] leading-relaxed text-white/90">{narrative}</p>
            </CardBody>
          </Card>
        )}

        {/* 지표 비교 */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Card>
            <CardBody>
              <SectionHeader title="전월 대비 변화" />
              <MetricRow label="주문건수" curr={num(c.order_count)} prev={num(p?.order_count)} delta={menu.order_growth_pct} />
              <MetricRow label="실매출" curr={won(c.real_sales)} prev={won(p?.real_sales)} delta={menu.sales_growth_pct} />
              <MetricRow label="순매출" curr={won(c.net_sales)} prev={won(p?.net_sales)} />
              <MetricRow label="매출이익" curr={won(c.gross_profit)} prev={won(p?.gross_profit)} />
              <MetricRow label="할인율" curr={`${menu.discount_rate_curr}`} fmt="%" prev={`${menu.discount_rate_prev}%`} delta={menu.discount_rate_delta} />
              <MetricRow label="이익률" curr={`${menu.profit_rate_curr}`} fmt="%" prev={`${menu.profit_rate_prev}%`} />
              <MetricRow label="판매 가맹점 수" curr={num(c.store_count)} prev={num(p?.store_count)} />
            </CardBody>
          </Card>

          {/* 가맹점별 증감표 */}
          <Card>
            <CardBody className="!p-0">
              <div className="px-5 pt-5">
                <SectionHeader title="가맹점별 증감" subtitle="당월 실매출 기준 정렬" />
              </div>
              <div className="max-h-[420px] overflow-auto">
                <table className="w-full border-collapse">
                  <thead className="sticky top-0 bg-ink-850">
                    <tr className="border-b border-line">
                      <th className="th">가맹점</th>
                      <th className="th text-right">당월</th>
                      <th className="th text-right">전월</th>
                      <th className="th text-right">증감</th>
                    </tr>
                  </thead>
                  <tbody>
                    {menu.by_store.map((s) => (
                      <tr key={s.store_code} className="border-b border-line/40">
                        <td className="td">{s.store_name}</td>
                        <td className="td text-right tabular-nums">{won(s.curr_real_sales)}</td>
                        <td className="td text-right tabular-nums text-muted">{won(s.prev_real_sales)}</td>
                        <td className={cn("td text-right tabular-nums", deltaClass(s.sales_delta_pct))}>
                          {s.sales_delta_pct == null ? "신규" : pct(s.sales_delta_pct)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardBody>
          </Card>
        </div>
      </div>
    </>
  );
}
