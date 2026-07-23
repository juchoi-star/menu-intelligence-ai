"use client";

import { usePCAnalysis } from "@/lib/pcStore";
import { Badge } from "@/components/ui/Badge";

export function PCTopbar({ title }: { title: string }) {
  const { result } = usePCAnalysis();
  return (
    <header className="sticky top-0 z-20 -mx-8 mb-6 flex items-center justify-between border-b border-line bg-ink-950/70 px-8 py-4 backdrop-blur-xl">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-white">{title}</h1>
        {result && (
          <p className="mt-0.5 text-sm text-muted">
            {result.meta.prev_label} → {result.meta.curr_label} · 상품 {result.meta.product_count.toLocaleString()}개
          </p>
        )}
      </div>
      <div className="flex items-center gap-2">
        {result ? (
          <>
            <Badge tone="gold">기준 {result.meta.curr_label}</Badge>
            <Badge tone={result.ai.provider === "openai" ? "gold" : "neutral"}>
              AI · {result.ai.provider}
            </Badge>
          </>
        ) : (
          <Badge tone="neutral">데이터 없음</Badge>
        )}
      </div>
    </header>
  );
}
