import type { Metadata } from "next";
import "./globals.css";
import { AnalysisProvider } from "@/lib/store";
import { Sidebar } from "@/components/layout/Sidebar";

export const metadata: Metadata = {
  title: "Menu Intelligence AI",
  description: "월별 POS 메뉴 매출 자동 비교 분석 BI 플랫폼",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body>
        <AnalysisProvider>
          <Sidebar />
          <main className="ml-60 min-h-screen px-8 pb-16 pt-0">{children}</main>
        </AnalysisProvider>
      </body>
    </html>
  );
}
