import Link from "next/link";
import { Card } from "@/components/ui/Card";

export function EmptyState({
  title = "분석 데이터가 없습니다",
  description = "대시보드에서 월별 POS 파일 2개를 업로드해 분석을 실행하세요.",
  showCta = true,
}: {
  title?: string;
  description?: string;
  showCta?: boolean;
}) {
  return (
    <Card>
      <div className="flex flex-col items-center justify-center gap-3 px-6 py-16 text-center">
        <div className="grid h-14 w-14 place-items-center rounded-2xl bg-accent/10 text-accent ring-1 ring-accent/20">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className="h-7 w-7">
            <path d="M3 3v18h18M7 15l4-4 3 3 5-6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-white">{title}</h3>
        <p className="max-w-sm text-sm text-muted">{description}</p>
        {showCta && (
          <Link
            href="/"
            className="mt-2 rounded-xl bg-accent px-4 py-2 text-sm font-semibold text-ink-950 hover:bg-accent-soft"
          >
            대시보드로 이동
          </Link>
        )}
      </div>
    </Card>
  );
}
