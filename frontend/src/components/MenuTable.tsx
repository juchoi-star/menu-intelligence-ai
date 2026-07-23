"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { GROUP_COLOR } from "@/components/GroupBreakdown";
import { won, num, pct, deltaClass } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { MenuAnalysis } from "@/types";

type SortKey = "real_sales" | "growth" | "orders" | "contribution";

export function MenuTable({ menus }: { menus: MenuAnalysis[] }) {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<SortKey>("real_sales");
  const [cat, setCat] = useState<string>("전체");

  const categories = useMemo(
    () => ["전체", ...Array.from(new Set(menus.map((m) => m.category)))],
    [menus],
  );

  const rows = useMemo(() => {
    let r = menus.filter(
      (m) =>
        (cat === "전체" || m.category === cat) &&
        (q === "" || m.menu_name.toLowerCase().includes(q.toLowerCase())),
    );
    const key = (m: MenuAnalysis) => {
      switch (sort) {
        case "growth":
          return m.sales_growth_pct ?? -Infinity;
        case "orders":
          return m.curr.order_count;
        case "contribution":
          return m.contribution_pct;
        default:
          return m.curr.real_sales;
      }
    };
    return [...r].sort((a, b) => key(b) - key(a));
  }, [menus, q, sort, cat]);

  return (
    <Card>
      <div className="flex flex-wrap items-center gap-3 border-b border-line px-5 py-3.5">
        <h3 className="text-sm font-semibold text-white">전체 메뉴 ({rows.length})</h3>
        <div className="ml-auto flex flex-wrap items-center gap-2">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="메뉴 검색…"
            className="w-40 rounded-lg border border-line bg-ink-800/60 px-3 py-1.5 text-sm text-white placeholder:text-muted/70 focus:border-accent/50 focus:outline-none"
          />
          <select
            value={cat}
            onChange={(e) => setCat(e.target.value)}
            className="rounded-lg border border-line bg-ink-800/60 px-2.5 py-1.5 text-sm text-white focus:outline-none"
          >
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as SortKey)}
            className="rounded-lg border border-line bg-ink-800/60 px-2.5 py-1.5 text-sm text-white focus:outline-none"
          >
            <option value="real_sales">실매출순</option>
            <option value="growth">성장률순</option>
            <option value="orders">주문건수순</option>
            <option value="contribution">기여도순</option>
          </select>
        </div>
      </div>

      <div className="max-h-[560px] overflow-auto">
        <table className="w-full border-collapse">
          <thead className="sticky top-0 z-10 bg-ink-850">
            <tr className="border-b border-line">
              <th className="th">메뉴</th>
              <th className="th">분류</th>
              <th className="th text-right">실매출</th>
              <th className="th text-right">성장률</th>
              <th className="th text-right">주문</th>
              <th className="th text-right">기여도</th>
              <th className="th text-right">순위</th>
              <th className="th">상태</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((m) => (
              <tr
                key={m.menu_code}
                onClick={() => router.push(`/sjp/menu/${encodeURIComponent(m.menu_code)}`)}
                className="row-hover cursor-pointer border-b border-line/40"
              >
                <td className="td font-medium">{m.menu_name}</td>
                <td className="td text-muted">
                  <span className="inline-flex items-center gap-1.5">
                    <span
                      className="h-2 w-2 rounded-full"
                      style={{ background: GROUP_COLOR[m.group] ?? "#8ba0bd" }}
                      title={m.group}
                    />
                    {m.category}
                  </span>
                </td>
                <td className="td text-right tabular-nums">{won(m.curr.real_sales)}</td>
                <td className={cn("td text-right tabular-nums", deltaClass(m.sales_growth_pct))}>
                  {m.sales_growth_pct == null ? "–" : pct(m.sales_growth_pct)}
                </td>
                <td className="td text-right tabular-nums">{num(m.curr.order_count)}</td>
                <td className="td text-right tabular-nums text-muted">{m.contribution_pct}%</td>
                <td className="td text-right tabular-nums">
                  {m.rank_curr ?? "–"}
                  {m.rank_change != null && m.rank_change !== 0 && (
                    <span className={cn("ml-1 text-xs", m.rank_change > 0 ? "text-pos" : "text-neg")}>
                      {m.rank_change > 0 ? `▲${m.rank_change}` : `▼${Math.abs(m.rank_change)}`}
                    </span>
                  )}
                </td>
                <td className="td">
                  {m.is_new && <Badge tone="accent">신규</Badge>}
                  {m.is_discontinued && <Badge tone="neg">중단</Badge>}
                  {m.grew_without_discount && <Badge tone="gold">할인X성장</Badge>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
