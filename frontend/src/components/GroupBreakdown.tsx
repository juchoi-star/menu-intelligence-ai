"use client";

import { Card, CardBody, SectionHeader } from "@/components/ui/Card";
import { won, wonShort, pct, deltaClass } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { GroupSlice } from "@/types";

// 그룹별 대표 색상
export const GROUP_COLOR: Record<string, string> = {
  주류: "#e5b567", // gold
  음식: "#5eead4", // teal
  기타: "#8ba0bd", // muted
};

export function GroupBreakdown({ groups }: { groups: GroupSlice[] }) {
  const total = groups.reduce((s, g) => s + g.real_sales_curr, 0) || 1;

  return (
    <Card>
      <CardBody>
        <SectionHeader title="그룹별 매출" subtitle="주류 · 음식 · 기타 분리 분석" />

        {/* 100% 누적 바 */}
        <div className="mb-5 flex h-3 w-full overflow-hidden rounded-full bg-white/[0.05]">
          {groups.map((g) => (
            <div
              key={g.group}
              title={`${g.group} ${g.contribution_pct}%`}
              style={{
                width: `${(g.real_sales_curr / total) * 100}%`,
                background: GROUP_COLOR[g.group] ?? "#8ba0bd",
              }}
            />
          ))}
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {groups.map((g) => (
            <div key={g.group} className="rounded-xl border border-line/60 bg-ink-800/40 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ background: GROUP_COLOR[g.group] ?? "#8ba0bd" }}
                  />
                  <span className="text-sm font-semibold text-white">{g.group}</span>
                </div>
                <span className="text-xs text-muted">{g.contribution_pct}%</span>
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-xl font-semibold text-white">{wonShort(g.real_sales_curr)}</span>
                <span className={cn("text-sm font-semibold", deltaClass(g.sales_delta_pct))}>
                  {g.sales_delta_pct != null && (g.sales_delta_pct > 0 ? "▲" : "▼")} {pct(g.sales_delta_pct, false)}
                </span>
              </div>
              <div className="mt-1.5 text-xs text-muted">
                {won(g.real_sales_curr)} · 이익률 {g.profit_rate_curr}% · 할인율 {g.discount_rate_curr}% · 메뉴 {g.menu_count_curr}
              </div>
            </div>
          ))}
        </div>
      </CardBody>
    </Card>
  );
}
