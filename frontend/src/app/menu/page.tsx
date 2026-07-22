"use client";

import { useMemo, useState } from "react";
import { useAnalysis } from "@/lib/store";
import { Topbar } from "@/components/layout/Topbar";
import { EmptyState } from "@/components/EmptyState";
import { InsightList } from "@/components/InsightList";
import { MenuTable } from "@/components/MenuTable";
import { SectionHeader } from "@/components/ui/Card";
import { GROUP_COLOR } from "@/components/GroupBreakdown";
import { cn } from "@/lib/utils";
import { won, pct } from "@/lib/format";
import type { Insights } from "@/types";

const ALL = "전체";

export default function MenuAnalysisPage() {
  const { result, hydrated } = useAnalysis();
  const [tab, setTab] = useState<string>(ALL);

  const tabs = useMemo(() => {
    if (!result) return [ALL];
    return [ALL, ...result.groups.map((g) => g.group)];
  }, [result]);

  if (!hydrated) return <><Topbar title="메뉴 분석" /></>;
  if (!result)
    return (
      <>
        <Topbar title="메뉴 분석" />
        <EmptyState />
      </>
    );

  const activeGroup = result.groups.find((g) => g.group === tab);
  const ins: Insights = activeGroup ? activeGroup.insights : result.insights;
  const menus = tab === ALL ? result.menus : result.menus.filter((m) => m.group === tab);
  const metrics = activeGroup?.metrics;

  return (
    <>
      <Topbar title="메뉴 분석" />
      <div className="space-y-6">
        {/* 그룹 탭 */}
        <div className="flex flex-wrap items-center gap-2">
          {tabs.map((t) => {
            const active = t === tab;
            const color = GROUP_COLOR[t];
            return (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={cn(
                  "flex items-center gap-2 rounded-xl border px-4 py-2 text-sm font-medium transition-all",
                  active
                    ? "border-accent/40 bg-accent/10 text-white"
                    : "border-line bg-ink-850/60 text-muted hover:text-white/90",
                )}
              >
                {color && <span className="h-2 w-2 rounded-full" style={{ background: color }} />}
                {t}
              </button>
            );
          })}
        </div>

        {/* 선택 그룹 요약 */}
        {metrics && (
          <div className="flex flex-wrap items-center gap-x-6 gap-y-1 rounded-xl border border-line/60 bg-ink-850/50 px-5 py-3 text-sm">
            <span className="font-semibold text-white">{metrics.group}</span>
            <span className="text-muted">실매출 <b className="text-white/90">{won(metrics.real_sales_curr)}</b> ({pct(metrics.sales_delta_pct)})</span>
            <span className="text-muted">비중 <b className="text-white/90">{metrics.contribution_pct}%</b></span>
            <span className="text-muted">이익률 <b className="text-white/90">{metrics.profit_rate_curr}%</b></span>
            <span className="text-muted">할인율 <b className="text-white/90">{metrics.discount_rate_curr}%</b></span>
            <span className="text-muted">판매메뉴 <b className="text-white/90">{metrics.menu_count_curr}</b></span>
          </div>
        )}

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <InsightList title="상승 TOP10" items={ins.rising_top10} tone="pos" />
          <InsightList title="하락 TOP10" items={ins.falling_top10} tone="neg" />
          <InsightList title={`매출 기여도 TOP10${tab === ALL ? "" : " (그룹 내)"}`} items={ins.top_contributors} tone="gold" />
          <InsightList title="주문 증가율 TOP10" items={ins.order_growth_top} tone="accent" />
          <InsightList title={`순위 상승${tab === ALL ? "" : " (그룹 내)"}`} items={ins.rank_up} tone="pos" />
          <InsightList title={`순위 하락${tab === ALL ? "" : " (그룹 내)"}`} items={ins.rank_down} tone="neg" />
          <InsightList
            title="할인 없이 성장한 메뉴"
            items={ins.grew_without_discount}
            tone="gold"
            emptyText="할인 감소에도 성장한 메뉴가 없습니다."
          />
          <InsightList title="신규 메뉴" items={ins.new_menus} tone="accent" />
          <InsightList
            title="판매 중단 메뉴"
            items={ins.discontinued_menus}
            tone="neutral"
            emptyText="판매 중단된 메뉴가 없습니다."
          />
        </div>

        <div>
          <SectionHeader
            title={`${tab === ALL ? "전체" : tab} 메뉴 탐색`}
            subtitle="검색·분류·정렬 후 클릭하면 상세로 이동합니다."
          />
          <MenuTable menus={menus} />
        </div>
      </div>
    </>
  );
}
