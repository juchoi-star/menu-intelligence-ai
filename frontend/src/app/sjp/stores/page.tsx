"use client";

import { useAnalysis } from "@/lib/store";
import { Topbar } from "@/components/layout/Topbar";
import { EmptyState } from "@/components/EmptyState";
import { Card, CardBody } from "@/components/ui/Card";
import { GROUP_COLOR } from "@/components/GroupBreakdown";
import { won, wonShort, pct, deltaClass } from "@/lib/format";
import { cn } from "@/lib/utils";

export default function StoresPage() {
  const { result, hydrated } = useAnalysis();

  if (!hydrated) return <><Topbar title="가맹점 분석" /></>;
  if (!result)
    return (
      <>
        <Topbar title="가맹점 분석" />
        <EmptyState />
      </>
    );

  const stores = result.stores.slice(0, 20);
  const maxSales = Math.max(...stores.map((s) => s.real_sales_curr), 1);

  return (
    <>
      <Topbar title="가맹점 분석" />
      <Card>
        <CardBody className="!p-0">
          <div className="border-b border-line px-5 py-3.5">
            <h3 className="text-sm font-semibold text-white">가맹점 TOP20 · 당월 실매출 기준</h3>
          </div>
          <div className="overflow-auto">
            <table className="w-full border-collapse">
              <thead className="bg-ink-850">
                <tr className="border-b border-line">
                  <th className="th">#</th>
                  <th className="th">가맹점</th>
                  <th className="th">실매출 (당월)</th>
                  <th className="th">주류 · 음식 구성</th>
                  <th className="th text-right">증감률</th>
                  <th className="th text-right">이익률</th>
                  <th className="th text-right">메뉴수</th>
                </tr>
              </thead>
              <tbody>
                {stores.map((s, i) => (
                  <tr key={s.store_code} className="row-hover border-b border-line/40">
                    <td className="td text-muted">{i + 1}</td>
                    <td className="td font-medium">{s.store_name}</td>
                    <td className="td">
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-28 overflow-hidden rounded-full bg-white/[0.06]">
                          <div
                            className="h-full rounded-full bg-accent"
                            style={{ width: `${(s.real_sales_curr / maxSales) * 100}%` }}
                          />
                        </div>
                        <span className="tabular-nums text-white/85">{won(s.real_sales_curr)}</span>
                      </div>
                    </td>
                    <td className="td">
                      <GroupComposition sales={s.group_sales_curr} total={s.real_sales_curr} />
                    </td>
                    <td className={cn("td text-right tabular-nums", deltaClass(s.sales_delta_pct))}>
                      {pct(s.sales_delta_pct)}
                    </td>
                    <td className="td text-right tabular-nums">{s.profit_rate_curr}%</td>
                    <td className="td text-right tabular-nums">{s.menu_count_curr}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardBody>
      </Card>
    </>
  );
}

const GROUP_ORDER = ["주류", "음식", "기타"];

/** 가맹점 매출의 주류/음식/기타 구성 미니 스택바 + 금액. */
function GroupComposition({
  sales,
  total,
}: {
  sales: Record<string, number>;
  total: number;
}) {
  const denom = total || 1;
  return (
    <div className="flex items-center gap-2">
      <div className="flex h-1.5 w-24 overflow-hidden rounded-full bg-white/[0.06]">
        {GROUP_ORDER.map((g) => {
          const v = sales[g] ?? 0;
          if (v <= 0) return null;
          return (
            <div
              key={g}
              title={`${g} ${won(v)}`}
              style={{ width: `${(v / denom) * 100}%`, background: GROUP_COLOR[g] }}
            />
          );
        })}
      </div>
      <span className="text-xs text-muted">
        주류 {wonShort(sales["주류"] ?? 0)} · 음식 {wonShort(sales["음식"] ?? 0)}
      </span>
    </div>
  );
}
