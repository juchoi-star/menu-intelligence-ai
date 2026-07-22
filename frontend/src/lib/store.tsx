"use client";

// 분석 결과 클라이언트 상태.
// 업로드 후 결과를 컨텍스트 + localStorage 에 보관해 페이지 이동/새로고침에도 유지.

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { AnalysisResult } from "@/types";

const STORAGE_KEY = "mi:analysis";
const STORAGE_ID = "mi:analysis_id";

interface AnalysisState {
  result: AnalysisResult | null;
  analysisId: string | null;
  setAnalysis: (result: AnalysisResult, id: string | null) => void;
  clear: () => void;
  hydrated: boolean;
}

const Ctx = createContext<AnalysisState | null>(null);

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);

  // 최초 마운트 시 localStorage 복원
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      const id = localStorage.getItem(STORAGE_ID);
      if (raw) setResult(JSON.parse(raw) as AnalysisResult);
      if (id) setAnalysisId(id);
    } catch {
      /* ignore */
    }
    setHydrated(true);
  }, []);

  const setAnalysis = (r: AnalysisResult, id: string | null) => {
    setResult(r);
    setAnalysisId(id);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(r));
      if (id) localStorage.setItem(STORAGE_ID, id);
    } catch {
      /* 용량 초과 등은 무시 */
    }
  };

  const clear = () => {
    setResult(null);
    setAnalysisId(null);
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(STORAGE_ID);
  };

  const value = useMemo(
    () => ({ result, analysisId, setAnalysis, clear, hydrated }),
    [result, analysisId, hydrated],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAnalysis(): AnalysisState {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAnalysis must be used within AnalysisProvider");
  return ctx;
}
