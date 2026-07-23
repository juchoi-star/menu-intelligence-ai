"use client";

import Link from "next/link";

interface BrandCard {
  href: string;
  name: string;
  tag: string;
  desc: string;
  accent: string;
  emoji: string;
}

const BRANDS: BrandCard[] = [
  {
    href: "/sjp",
    name: "생전포차",
    tag: "포차 · 11개 가맹점",
    desc: "가맹점 × 메뉴분류 × 메뉴 단위 분석. 주류/음식/기타 그룹, 할인·이익률, 가맹점별 증감까지.",
    accent: "#5eead4",
    emoji: "🍶",
  },
  {
    href: "/pc",
    name: "피씨 (PC방)",
    tag: "상품 판매 순위",
    desc: "상품 단위 매출·판매개수·객단가·순위 변화, 분류별 증감, 신규/중단 상품 분석.",
    accent: "#e5b567",
    emoji: "🎮",
  },
];

export default function BrandLanding() {
  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col justify-center px-6 py-16">
      <div className="mb-2 flex items-center gap-2.5">
        <div className="grid h-9 w-9 place-items-center rounded-xl bg-accent/15 ring-1 ring-accent/30">
          <span className="text-lg font-bold text-accent">M</span>
        </div>
        <div>
          <div className="text-sm font-semibold text-white">Menu Intelligence AI</div>
          <div className="text-[11px] tracking-wide text-muted">POS 기반 매출 자동 분석</div>
        </div>
      </div>

      <h1 className="mt-8 text-3xl font-semibold tracking-tight text-white">
        어떤 브랜드를 분석할까요?
      </h1>
      <p className="mt-2 text-muted">
        브랜드마다 POS 데이터 형식이 달라, 각각에 맞는 전용 분석으로 안내합니다.
      </p>

      <div className="mt-10 grid grid-cols-1 gap-5 sm:grid-cols-2">
        {BRANDS.map((b) => (
          <Link
            key={b.href}
            href={b.href}
            className="group relative overflow-hidden rounded-xl2 border border-line bg-ink-850/70 p-6 shadow-card transition-all hover:-translate-y-0.5 hover:border-accent/30 hover:shadow-glow"
          >
            <div
              className="pointer-events-none absolute -right-10 -top-10 h-28 w-28 rounded-full blur-2xl"
              style={{ background: `${b.accent}22` }}
            />
            <div className="text-3xl">{b.emoji}</div>
            <div className="mt-4 flex items-center gap-2">
              <h2 className="text-xl font-semibold text-white">{b.name}</h2>
              <span
                className="rounded-full px-2 py-0.5 text-[11px] font-medium"
                style={{ background: `${b.accent}1f`, color: b.accent }}
              >
                {b.tag}
              </span>
            </div>
            <p className="mt-2 text-sm leading-relaxed text-muted">{b.desc}</p>
            <div className="mt-5 inline-flex items-center gap-1 text-sm font-medium text-accent">
              분석 시작
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-4 w-4 transition-transform group-hover:translate-x-0.5">
                <path d="M5 12h14M13 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
          </Link>
        ))}
      </div>

      <p className="mt-10 text-center text-xs text-muted/70">
        전월 · 당월 POS 파일 2개를 올리면 AI가 전월 대비 증감을 자동 분석합니다.
      </p>
    </main>
  );
}
