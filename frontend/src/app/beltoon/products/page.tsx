"use client";

import { useBeltoonAnalysis } from "@/lib/beltoonStore";
import { BeltoonTopbar } from "@/components/beltoon/BeltoonTopbar";
import { EmptyState } from "@/components/EmptyState";
import { PCInsightList } from "@/components/pc/PCInsightList";
import { PCProductTable } from "@/components/pc/PCProductTable";
import { SectionHeader } from "@/components/ui/Card";

export default function BeltoonProductsPage() {
  const { result, hydrated } = useBeltoonAnalysis();

  if (!hydrated) return <><BeltoonTopbar title="상품 분석" /></>;
  if (!result)
    return (
      <>
        <BeltoonTopbar title="상품 분석" />
        <EmptyState description="벌툰 대시보드에서 월별 파일들을 업로드해 분석을 실행하세요." />
      </>
    );

  const ins = result.insights;
  return (
    <>
      <BeltoonTopbar title="상품 분석" />
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
