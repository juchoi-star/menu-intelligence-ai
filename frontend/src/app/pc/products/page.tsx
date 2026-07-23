"use client";

import { usePCAnalysis } from "@/lib/pcStore";
import { PCTopbar } from "@/components/pc/PCTopbar";
import { EmptyState } from "@/components/EmptyState";
import { PCInsightList } from "@/components/pc/PCInsightList";
import { PCProductTable } from "@/components/pc/PCProductTable";
import { SectionHeader } from "@/components/ui/Card";

export default function PCProductsPage() {
  const { result, hydrated } = usePCAnalysis();

  if (!hydrated) return <><PCTopbar title="상품 분석" /></>;
  if (!result)
    return (
      <>
        <PCTopbar title="상품 분석" />
        <EmptyState description="PC 대시보드에서 월별 POS 파일 2개를 업로드해 분석을 실행하세요." />
      </>
    );

  const ins = result.insights;
  return (
    <>
      <PCTopbar title="상품 분석" />
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <PCInsightList title="매출 상승 TOP10" items={ins.rising_top10} tone="pos" />
          <PCInsightList title="매출 하락 TOP10" items={ins.falling_top10} tone="neg" />
          <PCInsightList title="매출 기여 TOP10" items={ins.top_contributors} tone="gold" />
          <PCInsightList title="판매개수 증가 TOP10" items={ins.qty_growth_top} tone="accent" />
          <PCInsightList title="순위 상승" items={ins.rank_up} tone="pos" />
          <PCInsightList title="순위 하락" items={ins.rank_down} tone="neg" />
          <PCInsightList title="신규 상품" items={ins.new_products} tone="accent" emptyText="신규 상품이 없습니다." />
          <PCInsightList title="판매 중단 상품" items={ins.discontinued_products} tone="neutral" emptyText="판매 중단 상품이 없습니다." />
        </div>

        <div>
          <SectionHeader title="상품 탐색" subtitle="검색·정렬 가능 (상위 매출 800개 표시)" />
          <PCProductTable products={result.products} />
        </div>
      </div>
    </>
  );
}
