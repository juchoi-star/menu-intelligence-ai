"use client";

import { useRef, useState } from "react";
import { comparePCFiles } from "@/lib/pcApi";
import { usePCAnalysis } from "@/lib/pcStore";
import { Card } from "@/components/ui/Card";

function FileSlot({
  label,
  file,
  onPick,
}: {
  label: string;
  file: File | null;
  onPick: (f: File | null) => void;
}) {
  const ref = useRef<HTMLInputElement>(null);
  return (
    <button
      type="button"
      onClick={() => ref.current?.click()}
      className="group flex flex-1 items-center gap-3 rounded-xl border border-dashed border-line bg-ink-800/40 px-4 py-4 text-left transition-colors hover:border-gold/40 hover:bg-ink-800/70"
    >
      <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-gold/10 text-gold ring-1 ring-gold/20">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" className="h-5 w-5">
          <path d="M14 3v4a1 1 0 0 0 1 1h4M17 21H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5v11a2 2 0 0 1-2 2Z" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <div className="min-w-0">
        <div className="text-xs font-medium uppercase tracking-wider text-muted">{label}</div>
        <div className="truncate text-sm text-white/90">
          {file ? file.name : "PC POS 파일 선택 (.xls)"}
        </div>
      </div>
      <input
        ref={ref}
        type="file"
        accept=".xls,.html,.htm,.xlsx"
        className="hidden"
        onChange={(e) => onPick(e.target.files?.[0] ?? null)}
      />
    </button>
  );
}

export function PCUploadPanel() {
  const { setAnalysis } = usePCAnalysis();
  const [prev, setPrev] = useState<File | null>(null);
  const [curr, setCurr] = useState<File | null>(null);
  const [prevLabel, setPrevLabel] = useState("전월");
  const [currLabel, setCurrLabel] = useState("당월");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    if (!prev || !curr) {
      setError("전월/당월 두 파일을 모두 선택하세요.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await comparePCFiles(prev, curr, prevLabel || "전월", currLabel || "당월");
      setAnalysis(res.result, res.analysis_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "분석 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <div className="card-pad">
        <div className="mb-4">
          <h3 className="text-base font-semibold text-white">PC 상품 판매 비교 분석</h3>
          <p className="mt-0.5 text-sm text-muted">
            전월·당월 &lsquo;매장통계 &gt; 상품 &gt; 순위&rsquo; 파일(.xls)을 올리면 상품별 전월 대비 증감을 분석합니다.
            <span className="text-muted/80"> (파일에 기간 표기가 없어 아래 라벨로 월을 구분합니다)</span>
          </p>
        </div>

        <div className="mb-3 flex flex-col gap-3 sm:flex-row">
          <div className="flex-1">
            <input
              value={prevLabel}
              onChange={(e) => setPrevLabel(e.target.value)}
              placeholder="전월 라벨 (예: 6월)"
              className="mb-1.5 w-full rounded-lg border border-line bg-ink-800/60 px-3 py-1.5 text-xs text-white placeholder:text-muted/60 focus:outline-none"
            />
            <FileSlot label="전월 (Prev)" file={prev} onPick={setPrev} />
          </div>
          <div className="flex-1">
            <input
              value={currLabel}
              onChange={(e) => setCurrLabel(e.target.value)}
              placeholder="당월 라벨 (예: 7월)"
              className="mb-1.5 w-full rounded-lg border border-line bg-ink-800/60 px-3 py-1.5 text-xs text-white placeholder:text-muted/60 focus:outline-none"
            />
            <FileSlot label="당월 (Curr)" file={curr} onPick={setCurr} />
          </div>
        </div>

        {error && (
          <div className="mt-1 rounded-lg border border-neg/30 bg-neg/10 px-3 py-2 text-sm text-neg">
            {error}
          </div>
        )}

        <div className="mt-4 flex items-center justify-end">
          <button
            type="button"
            onClick={run}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-xl bg-gold px-5 py-2.5 text-sm font-semibold text-ink-950 transition-all hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? (
              <>
                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="3" opacity="0.25" />
                  <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
                </svg>
                분석 중…
              </>
            ) : (
              "분석 실행"
            )}
          </button>
        </div>
      </div>
    </Card>
  );
}
