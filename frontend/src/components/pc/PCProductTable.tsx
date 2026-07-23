"use client";

import { useMemo, useState } from "react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { won, num, pct, deltaClass } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { PCProductAnalysis } from "@/types/pc";

type SortKey = "sales" | "growth" | "qty" | "rank";

export function PCProductTable({ products }: { products: PCProductAnalysis[] }) {
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<SortKey>("sales");

  const rows = useMemo(() => {
    const filtered = products.filter(
      (p) => q === "" || p.name.toLowerCase().includes(q.toLowerCase()),
    );
    const key = (p: PCProductAnalysis) => {
      switch (sort) {
        case "growth":
          return p.sales_growth_pct ?? -Infinity;
        case "qty":
          return p.curr.qty;
        case "rank":
          return -(p.rank_curr ?? 999999);
        default:
          return p.curr.sales;
      }
    };
    return [...filtered].sort((a, b) => key(b) - key(a));
  }, [products, q, sort]);

  return (
    <Card>
      <div className="flex flex-wrap items-center gap-3 border-b border-line px-5 py-3.5">
        <h3 className="text-sm font-semibold text-white">상품 목록 ({rows.length})</h3>
        <div className="ml-auto flex flex-wrap items-center gap-2">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="상품 검색…"
            className="w-44 rounded-lg border border-line bg-ink-800/60 px-3 py-1.5 text-sm text-white placeholder:text-muted/70 focus:border-gold/50 focus:outline-none"
          />
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as SortKey)}
            className="rounded-lg border border-line bg-ink-800/60 px-2.5 py-1.5 text-sm text-white focus:outline-none"
          >
            <option value="sales">매출순</option>
            <option value="growth">성장률순</option>
            <option value="qty">판매개수순</option>
            <option value="rank">순위순</option>
          </select>
        </div>
      </div>

      <div className="max-h-[560px] overflow-auto">
        <table className="w-full border-collapse">
          <thead className="sticky top-0 z-10 bg-ink-850">
            <tr className="border-b border-line">
              <th className="th">상품</th>
              <th className="th text-right">매출</th>
              <th className="th text-right">성장률</th>
              <th className="th text-right">판매개수</th>
              <th className="th text-right">객단가</th>
              <th className="th text-right">점유</th>
              <th className="th text-right">순위</th>
              <th className="th">상태</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => (
              <tr key={p.name} className="row-hover border-b border-line/40">
                <td className="td font-medium">{p.name}</td>
                <td className="td text-right tabular-nums">{won(p.curr.sales)}</td>
                <td className={cn("td text-right tabular-nums", deltaClass(p.sales_growth_pct))}>
                  {p.sales_growth_pct == null ? "–" : pct(p.sales_growth_pct)}
                </td>
                <td className="td text-right tabular-nums">{num(p.curr.qty)}</td>
                <td className="td text-right tabular-nums text-muted">{won(p.unit_price_curr)}</td>
                <td className="td text-right tabular-nums text-muted">{p.contribution_pct}%</td>
                <td className="td text-right tabular-nums">
                  {p.rank_curr ?? "–"}
                  {p.rank_change != null && p.rank_change !== 0 && (
                    <span className={cn("ml-1 text-xs", p.rank_change > 0 ? "text-pos" : "text-neg")}>
                      {p.rank_change > 0 ? `▲${p.rank_change}` : `▼${Math.abs(p.rank_change)}`}
                    </span>
                  )}
                </td>
                <td className="td">
                  {p.is_new && <Badge tone="accent">신규</Badge>}
                  {p.is_discontinued && <Badge tone="neg">중단</Badge>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
