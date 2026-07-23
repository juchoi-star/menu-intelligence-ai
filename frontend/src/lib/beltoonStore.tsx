"use client";

// 벌툰 분석 결과 상태 (PC와 동일한 결과 타입, 별도 localStorage 키).

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { PCAnalysisResult } from "@/types/pc";

const STORAGE_KEY = "mi:beltoon:analysis";
const STORAGE_ID = "mi:beltoon:analysis_id";

interface State {
  result: PCAnalysisResult | null;
  analysisId: string | null;
  setAnalysis: (result: PCAnalysisResult, id: string | null) => void;
  clear: () => void;
  hydrated: boolean;
}

const Ctx = createContext<State | null>(null);

export function BeltoonAnalysisProvider({ children }: { children: ReactNode }) {
  const [result, setResult] = useState<PCAnalysisResult | null>(null);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      const id = localStorage.getItem(STORAGE_ID);
      if (raw) setResult(JSON.parse(raw) as PCAnalysisResult);
      if (id) setAnalysisId(id);
    } catch {
      /* ignore */
    }
    setHydrated(true);
  }, []);

  const setAnalysis = (r: PCAnalysisResult, id: string | null) => {
    setResult(r);
    setAnalysisId(id);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(r));
      if (id) localStorage.setItem(STORAGE_ID, id);
    } catch {
      /* ignore */
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

export function useBeltoonAnalysis(): State {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useBeltoonAnalysis must be used within BeltoonAnalysisProvider");
  return ctx;
}
