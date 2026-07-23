// 브랜드별 수동 별칭표 API.

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export interface AliasGroup {
  canonical: string;
  members: string[];
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `요청 실패 (${res.status})`;
    try {
      const b = await res.json();
      if (b?.detail) detail = b.detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export async function getAliases(brand: string): Promise<AliasGroup[]> {
  const res = await fetch(`${API_BASE}/aliases/${brand}`);
  const body = await handle<{ groups: AliasGroup[] }>(res);
  return body.groups;
}

export async function putAliases(brand: string, groups: AliasGroup[]): Promise<AliasGroup[]> {
  const res = await fetch(`${API_BASE}/aliases/${brand}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ groups }),
  });
  const body = await handle<{ groups: AliasGroup[] }>(res);
  return body.groups;
}

/** 텍스트("대표명 = 변형1, 변형2") ↔ 그룹 변환 */
export function parseAliasText(text: string): AliasGroup[] {
  const groups: AliasGroup[] = [];
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line || !line.includes("=")) continue;
    const idx = line.indexOf("=");
    const canonical = line.slice(0, idx).trim();
    if (!canonical) continue;
    const members = line
      .slice(idx + 1)
      .split(",")
      .map((m) => m.trim())
      .filter(Boolean);
    // 대표명 자신도 멤버에 포함(중복 제거)
    const set = Array.from(new Set([canonical, ...members]));
    groups.push({ canonical, members: set });
  }
  return groups;
}

export function aliasGroupsToText(groups: AliasGroup[]): string {
  return groups
    .map((g) => {
      const others = g.members.filter((m) => m !== g.canonical);
      return `${g.canonical} = ${others.join(", ")}`;
    })
    .join("\n");
}
