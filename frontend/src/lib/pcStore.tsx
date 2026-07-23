"use client";

// 피씨(PC방) 분석 결과 클라이언트 상태 (생전포차와 분리된 localStorage 키).

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { PCAnalysisResult } from "@/types/pc";

const STORAGE_KEY = "mi:pc:analysis";
const STORAGE_ID = "mi:pc:analysis_id";

interface PCState {
  result: PCAnalysisResult | null;
  analysisId: string | null;
  setAnalysis: (result: PCAnalysisResult, id: string | null) => void;
  clear: () => void;
  hydrated: boolean;
}

const Ctx = createContext<PCState | null>(null);

export function PCAnalysisProvider({ children }: { children: ReactNode }) {
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
      /* 용량 초과 등 무시 */
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

export function usePCAnalysis(): PCState {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("usePCAnalysis must be used within PCAnalysisProvider");
  return ctx;
}
