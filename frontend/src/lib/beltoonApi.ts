// 벌툰 백엔드 API 클라이언트 (전월/당월 각각 여러 파일 업로드).

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

/** 전월/당월 각각 여러 개의 벌툰 파일을 업로드해 합산 비교 분석. */
export async function compareBeltoonFiles(
  prevFiles: File[],
  currFiles: File[],
  prevLabel = "전월",
  currLabel = "당월",
): Promise<PCUploadResponse> {
  const form = new FormData();
  prevFiles.forEach((f) => form.append("prev_files", f));
  currFiles.forEach((f) => form.append("curr_files", f));
  form.append("prev_label", prevLabel);
  form.append("curr_label", currLabel);
  const res = await fetch(`${API_BASE}/beltoon/compare`, { method: "POST", body: form });
  return handle<PCUploadResponse>(res);
}

export async function getBeltoonAnalysis(id: string): Promise<PCAnalysisResult> {
  const res = await fetch(`${API_BASE}/beltoon/${id}`);
  return handle<PCAnalysisResult>(res);
}
