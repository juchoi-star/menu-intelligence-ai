// 피씨(PC방) 백엔드 API 클라이언트.

import type { PCAnalysisResult, PCUploadResponse } from "@/types/pc";

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

/** 두 개의 월별 피씨 POS(.xls/HTML) 파일을 비교 분석. */
export async function comparePCFiles(
  prevFile: File,
  currFile: File,
  prevLabel = "전월",
  currLabel = "당월",
): Promise<PCUploadResponse> {
  const form = new FormData();
  form.append("prev_file", prevFile);
  form.append("curr_file", currFile);
  form.append("prev_label", prevLabel);
  form.append("curr_label", currLabel);
  const res = await fetch(`${API_BASE}/pc/compare`, { method: "POST", body: form });
  return handle<PCUploadResponse>(res);
}

export async function getPCAnalysis(id: string): Promise<PCAnalysisResult> {
  const res = await fetch(`${API_BASE}/pc/${id}`);
  return handle<PCAnalysisResult>(res);
}
