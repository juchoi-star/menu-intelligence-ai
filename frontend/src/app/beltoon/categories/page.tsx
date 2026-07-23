"use client";

import { useBeltoonAnalysis } from "@/lib/beltoonStore";
import { BeltoonTopbar } from "@/components/beltoon/BeltoonTopbar";
import { EmptyState } from "@/components/EmptyState";
import { PCCategoryChart } from "@/components/pc/PCCategoryChart";
import { Card, CardBody, SectionHeader } from "@/components/ui/Card";
import { won, num, pct, deltaClass } from "@/lib/format";
import { cn } from "@/lib/utils";

export default function BeltoonCategoriesPage() {
  const { result, hydrated } = useBeltoonAnalysis();

  if (!hydrated) return <><BeltoonTopbar title="분류 분석" /></>;
  if (!result)
    return (
      <>
        <BeltoonTopbar title="분류 분석" />
        <EmptyState description="벌툰 대시보드에서 월별 파일들을 업로드해 분석을 실행하세요." />
      </>
    );

  const cats = result.categories.filter((c) => c.curr > 0 || c.prev > 0);

  return (
    <>
      <BeltoonTopbar title="분류 분석" />
      <div className="space-y-6">
        <Card>
          <CardBody>
            <SectionHeader title="분류별 매출 비교" subtitle="당월 vs 전월 (상위 12)" />
            <PCCategoryChart data={result.categories} />
          </CardBody>
        </Card>

        <Card>
          <CardBody className="!p-0">
            <div className="border-b border-line px-5 py-3.5">
              <h3 className="text-sm font-semibold text-white">전체 분류 ({cats.length})</h3>
            </div>
            <div className="max-h-[560px] overflow-auto">
              <table className="w-full border-collapse">
                <thead className="sticky top-0 z-10 bg-ink-850">
                  <tr className="border-b border-line">
                    <th className="th">#</th>
                    <th className="th">분류</th>
                    <th className="th text-right">당월 매출</th>
                    <th className="th text-right">전월 매출</th>
                    <th className="th text-right">증감률</th>
                    <th className="th text-right">당월 판매개수</th>
                  </tr>
                </thead>
                <tbody>
                  {cats.map((c, i) => (
                    <tr key={c.name} className="row-hover border-b border-line/40">
                      <td className="td text-muted">{i + 1}</td>
                      <td className="td font-medium">{c.name}</td>
                      <td className="td text-right tabular-nums">{won(c.curr)}</td>
                      <td className="td text-right tabular-nums text-muted">{won(c.prev)}</td>
                      <td className={cn("td text-right tabular-nums", deltaClass(c.delta_pct))}>
                        {c.delta_pct == null ? "신규" : pct(c.delta_pct)}
                      </td>
                      <td className="td text-right tabular-nums text-muted">{num(c.qty_curr)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      </div>
    </>
  );
}
