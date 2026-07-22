// 백엔드 API 클라이언트.

import type { AnalysisResult, UploadResponse } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `요청 실패 (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

/** 두 개의 월별 POS 엑셀을 업로드해 비교 분석. */
export async function compareFiles(
  prevFile: File,
  currFile: File,
): Promise<UploadResponse> {
  const form = new FormData();
  form.append("prev_file", prevFile);
  form.append("curr_file", currFile);
  const res = await fetch(`${API_BASE}/analysis/compare`, {
    method: "POST",
    body: form,
  });
  return handle<UploadResponse>(res);
}

export async function getAnalysis(id: string): Promise<AnalysisResult> {
  const res = await fetch(`${API_BASE}/analysis/${id}`);
  return handle<AnalysisResult>(res);
}

export function reportPdfUrl(id: string): string {
  return `${API_BASE}/analysis/${id}/report.pdf`;
}
