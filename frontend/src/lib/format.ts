// 숫자/통화/퍼센트 표기 유틸.

export function won(value: number | null | undefined): string {
  if (value == null) return "-";
  return `${Math.round(value).toLocaleString("ko-KR")}원`;
}

export function wonShort(value: number | null | undefined): string {
  if (value == null) return "-";
  const abs = Math.abs(value);
  if (abs >= 100_000_000) return `${(value / 100_000_000).toFixed(1)}억`;
  if (abs >= 10_000) return `${(value / 10_000).toFixed(0)}만`;
  return Math.round(value).toLocaleString("ko-KR");
}

export function num(value: number | null | undefined): string {
  if (value == null) return "-";
  return Math.round(value).toLocaleString("ko-KR");
}

export function pct(value: number | null | undefined, withSign = true): string {
  if (value == null) return "-";
  const sign = withSign && value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}

/** 증감 방향에 따른 색상 클래스 */
export function deltaClass(value: number | null | undefined): string {
  if (value == null) return "text-muted";
  if (value > 0) return "text-pos";
  if (value < 0) return "text-neg";
  return "text-muted";
}
