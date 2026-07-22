"use client";

import { Topbar } from "@/components/layout/Topbar";
import { Card, CardBody } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

const PLANNED = [
  {
    title: "Weather API",
    desc: "기온·강수 등 날씨 데이터를 매출과 상관 분석. 폭염/한파 시 특정 메뉴 수요 변화 추적.",
  },
  {
    title: "News API",
    desc: "식자재 가격, 트렌드, 지역 이슈 등 외부 뉴스를 수집해 매출 변동의 외부 요인을 설명.",
  },
];

export default function ExternalPage() {
  return (
    <>
      <Topbar title="외부요인" />
      <Card>
        <CardBody className="py-14 text-center">
          <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-gold/10 text-gold ring-1 ring-gold/20">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className="h-7 w-7">
              <path d="M12 3a9 9 0 1 0 9 9M12 3v9l6 3M12 3a9 9 0 0 1 9 9" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <h3 className="mt-4 text-lg font-semibold text-white">외부 요인 분석 (준비 중)</h3>
          <p className="mx-auto mt-1 max-w-md text-sm text-muted">
            날씨·뉴스 등 외부 데이터를 연결해 매출 변동의 배경을 설명하는 기능이 곧 추가됩니다.
          </p>

          <div className="mx-auto mt-8 grid max-w-2xl grid-cols-1 gap-3 sm:grid-cols-2">
            {PLANNED.map((p) => (
              <div key={p.title} className="rounded-xl border border-line/60 bg-ink-800/40 p-4 text-left">
                <div className="mb-1.5 flex items-center gap-2">
                  <span className="text-sm font-semibold text-white">{p.title}</span>
                  <Badge tone="neutral">예정</Badge>
                </div>
                <p className="text-sm leading-relaxed text-muted">{p.desc}</p>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>
    </>
  );
}
