"use client";

import { useAnalysis } from "@/lib/store";
import { Topbar } from "@/components/layout/Topbar";
import { Card, CardBody, SectionHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export default function SettingsPage() {
  const { result, analysisId, clear, hydrated } = useAnalysis();

  return (
    <>
      <Topbar title="설정" />
      <div className="max-w-2xl space-y-6">
        <Card>
          <CardBody>
            <SectionHeader title="연결 정보" />
            <Row label="API Base URL" value={API_BASE} />
            <Row
              label="AI 제공자"
              value={result?.ai.provider ?? "-"}
              badge={result?.ai.provider === "openai" ? "gold" : "neutral"}
            />
            <Row label="현재 분석 ID" value={analysisId ?? "없음"} />
            <Row label="기준월" value={result ? `${result.meta.prev_label} → ${result.meta.curr_label}` : "-"} />
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <SectionHeader title="데이터 관리" subtitle="브라우저에 저장된 분석 결과를 초기화합니다." />
            <button
              onClick={clear}
              disabled={!hydrated || !result}
              className="rounded-xl border border-neg/30 bg-neg/10 px-4 py-2 text-sm font-medium text-neg transition-colors hover:bg-neg/20 disabled:cursor-not-allowed disabled:opacity-40"
            >
              분석 데이터 초기화
            </button>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <SectionHeader title="OpenAI 연동" subtitle="백엔드 .env 에 OPENAI_API_KEY 설정 시 GPT 내러티브가 활성화됩니다." />
            <p className="text-sm leading-relaxed text-muted">
              키가 없으면 규칙 기반(rule-based) 내러티브로 자동 폴백되어 오프라인에서도 완전히 동작합니다.
              모델은 <code className="rounded bg-white/[0.06] px-1.5 py-0.5 text-white/80">OPENAI_MODEL</code> 로 변경할 수 있습니다.
            </p>
          </CardBody>
        </Card>
      </div>
    </>
  );
}

function Row({
  label,
  value,
  badge,
}: {
  label: string;
  value: string;
  badge?: "gold" | "neutral";
}) {
  return (
    <div className="flex items-center justify-between border-b border-line/50 py-3 last:border-0">
      <span className="text-sm text-muted">{label}</span>
      {badge ? (
        <Badge tone={badge}>{value}</Badge>
      ) : (
        <span className="max-w-[60%] truncate text-sm text-white/85">{value}</span>
      )}
    </div>
  );
}
