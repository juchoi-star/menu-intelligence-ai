"use client";

import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { won } from "@/lib/format";
import type { PCInsightItem } from "@/types/pc";

export function PCInsightList({
  title,
  items,
  tone = "gold",
  emptyText = "해당 항목이 없습니다.",
}: {
  title: string;
  items: PCInsightItem[];
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
          <div key={`${it.name}-${i}`} className="flex items-center gap-3 px-5 py-3">
            <span className="w-5 shrink-0 text-center text-xs font-semibold text-muted">{i + 1}</span>
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-medium text-white/90">{it.name}</div>
              <div className="mt-0.5 truncate text-xs text-muted">{it.detail}</div>
            </div>
            <div className="shrink-0 text-right">
              <div className="text-sm font-semibold text-white/90">{won(it.curr_sales)}</div>
              <div className="text-[11px] text-muted">전월 {won(it.prev_sales)}</div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
