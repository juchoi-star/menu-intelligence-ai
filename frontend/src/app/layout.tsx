import type { Metadata } from "next";
import "./globals.css";
import { AnalysisProvider } from "@/lib/store";
import { PCAnalysisProvider } from "@/lib/pcStore";
import { BeltoonAnalysisProvider } from "@/lib/beltoonStore";

export const metadata: Metadata = {
  title: "Menu Intelligence AI",
  description: "월별 POS 매출 자동 비교 분석 BI 플랫폼 (생전포차 · 피씨)",
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
          <PCAnalysisProvider>
            <BeltoonAnalysisProvider>{children}</BeltoonAnalysisProvider>
          </PCAnalysisProvider>
        </AnalysisProvider>
      </body>
    </html>
  );
}
