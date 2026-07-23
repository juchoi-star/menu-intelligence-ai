"use client";

import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { won } from "@/lib/format";
import type { MenuInsightItem } from "@/types";

export function InsightList({
  title,
  items,
  tone = "accent",
  emptyText = "해당 항목이 없습니다.",
}: {
  title: string;
  items: MenuInsightItem[];
  tone?: "pos" | "neg" | "accent" | "gold" | "neutral";
  emptyText?: string;
}) {
  return (
    <Card className="flex flex-col">
      <div className="flex items-center justify-between border-b border-line px-5 py-3.5">
        <h3 className="text-sm font-semibold text-white">{title}</h3>
        <Badge tone={tone}>{items.length}</Badge>
      </div>
      <div className="divide-y divide-line/60">
        {items.length === 0 && (
          <div className="px-5 py-6 text-center text-sm text-muted">{emptyText}</div>
        )}
        {items.map((it, i) => (
          <Link
            key={`${it.menu_code}-${i}`}
            href={`/sjp/menu/${encodeURIComponent(it.menu_code)}`}
            className="row-hover flex items-center gap-3 px-5 py-3"
          >
            <span className="w-5 shrink-0 text-center text-xs font-semibold text-muted">
              {i + 1}
            </span>
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-medium text-white/90">{it.menu_name}</div>
              <div className="mt-0.5 flex items-center gap-2 text-xs text-muted">
                <span className="rounded bg-white/[0.05] px-1.5 py-0.5">{it.category}</span>
                <span className="truncate">{it.detail}</span>
              </div>
            </div>
            <div className="shrink-0 text-right">
              <div className="text-sm font-semibold text-white/90">{won(it.curr_real_sales)}</div>
              <div className="text-[11px] text-muted">전월 {won(it.prev_real_sales)}</div>
            </div>
          </Link>
        ))}
      </div>
    </Card>
  );
}
