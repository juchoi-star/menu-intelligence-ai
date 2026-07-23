"use client";

import { useRef, useState } from "react";
import { compareBeltoonFiles } from "@/lib/beltoonApi";
import { useBeltoonAnalysis } from "@/lib/beltoonStore";
import { Card } from "@/components/ui/Card";

const VIOLET = "#a78bfa";

function MultiFileSlot({
  label,
  files,
  onPick,
}: {
  label: string;
  files: File[];
  onPick: (f: File[]) => void;
}) {
  const ref = useRef<HTMLInputElement>(null);
  return (
    <div className="flex-1">
      <button
        type="button"
        onClick={() => ref.current?.click()}
        className="group flex w-full items-center gap-3 rounded-xl border border-dashed border-line bg-ink-800/40 px-4 py-4 text-left transition-colors hover:bg-ink-800/70"
        style={{ borderColor: files.length ? `${VIOLET}66` : undefined }}
      >
        <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg" style={{ background: `${VIOLET}1f`, color: VIOLET }}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" className="h-5 w-5">
            <path d="M14 3v4a1 1 0 0 0 1 1h4M17 21H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5v11a2 2 0 0 1-2 2Z" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <div className="min-w-0">
          <div className="text-xs font-medium uppercase tracking-wider text-muted">{label}</div>
          <div className="truncate text-sm text-white/90">
            {files.length ? `${files.length}개 파일 선택됨` : "엑셀 파일 선택 (여러 개 가능)"}
          </div>
        </div>
      </button>
      {files.length > 0 && (
        <ul className="mt-1.5 space-y-1">
          {files.map((f, i) => (
            <li key={i} className="truncate rounded-md bg-white/[0.04] px-2.5 py-1 text-[11px] text-muted">
              {f.name}
            </li>
          ))}
        </ul>
      )}
      <input
        ref={ref}
        type="file"
        accept=".xlsx,.xlsm"
        multiple
        className="hidden"
        onChange={(e) => onPick(Array.from(e.target.files ?? []))}
      />
    </div>
  );
}

export function BeltoonUploadPanel() {
  const { setAnalysis } = useBeltoonAnalysis();
  const [prev, setPrev] = useState<File[]>([]);
  const [curr, setCurr] = useState<File[]>([]);
  const [prevLabel, setPrevLabel] = useState("전월");
  const [currLabel, setCurrLabel] = useState("당월");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    if (!prev.length || !curr.length) {
      setError("전월/당월 파일을 각각 1개 이상 선택하세요.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await compareBeltoonFiles(prev, curr, prevLabel || "전월", currLabel || "당월");
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
          <h3 className="text-base font-semibold text-white">벌툰 상품 매출 비교 분석</h3>
          <p className="mt-0.5 text-sm text-muted">
            용량이 큰 벌툰은 한 달 데이터가 여러 파일로 나뉩니다. 전월·당월 각각 <b className="text-white/80">여러 파일을 함께 선택</b>하면 자동으로 합산해 분석합니다.
          </p>
        </div>

        <div className="mb-3 flex flex-col gap-4 sm:flex-row">
          <div className="flex-1">
            <input
              value={prevLabel}
              onChange={(e) => setPrevLabel(e.target.value)}
              placeholder="전월 라벨 (예: 5월)"
              className="mb-1.5 w-full rounded-lg border border-line bg-ink-800/60 px-3 py-1.5 text-xs text-white placeholder:text-muted/60 focus:outline-none"
            />
            <MultiFileSlot label="전월 (Prev)" files={prev} onPick={setPrev} />
          </div>
          <div className="flex-1">
            <input
              value={currLabel}
              onChange={(e) => setCurrLabel(e.target.value)}
              placeholder="당월 라벨 (예: 6월)"
              className="mb-1.5 w-full rounded-lg border border-line bg-ink-800/60 px-3 py-1.5 text-xs text-white placeholder:text-muted/60 focus:outline-none"
            />
            <MultiFileSlot label="당월 (Curr)" files={curr} onPick={setCurr} />
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
            className="inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold text-ink-950 transition-all hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
            style={{ background: VIOLET }}
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
