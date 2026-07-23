"use client";

import { useEffect, useState } from "react";
import { Card, CardBody, SectionHeader } from "@/components/ui/Card";
import {
  aliasGroupsToText,
  getAliases,
  parseAliasText,
  putAliases,
} from "@/lib/aliasApi";

/** 브랜드별 수동 별칭표 편집기 (텍스트 방식). */
export function AliasManager({ brand, brandName }: { brand: string; brandName: string }) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  useEffect(() => {
    getAliases(brand)
      .then((groups) => setText(aliasGroupsToText(groups)))
      .catch((e) => setMsg({ kind: "err", text: e.message }))
      .finally(() => setLoading(false));
  }, [brand]);

  const groups = parseAliasText(text);

  async function save() {
    setSaving(true);
    setMsg(null);
    try {
      const saved = await putAliases(brand, parseAliasText(text));
      setText(aliasGroupsToText(saved));
      setMsg({ kind: "ok", text: `저장됨 · ${saved.length}개 그룹. 다음 분석부터 적용됩니다.` });
    } catch (e) {
      setMsg({ kind: "err", text: e instanceof Error ? e.message : "저장 실패" });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-white">별칭 설정 · {brandName}</h1>
        <p className="mt-1 text-sm text-muted">
          이름이 다르지만 같은 메뉴를 하나로 합칩니다. (공백·괄호·대소문자는 자동 병합되고, 여기선 그 외 동의어를 등록)
        </p>
      </div>

      <Card>
        <CardBody>
          <SectionHeader
            title="별칭 규칙"
            subtitle="한 줄에 한 그룹:  대표명 = 변형1, 변형2, 변형3"
          />
          <div className="mb-3 rounded-lg border border-line/60 bg-ink-800/40 p-3 text-xs leading-relaxed text-muted">
            예시:<br />
            <code className="text-white/80">아이스 아메리카노 = 아이스아메리카노, 아메리카노(ice), 차가운 아메리카노</code>
            <br />
            <code className="text-white/80">감자튀김 = 감튀, 감자 튀김</code>
          </div>

          {loading ? (
            <div className="py-10 text-center text-sm text-muted">불러오는 중…</div>
          ) : (
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              spellCheck={false}
              placeholder="대표명 = 변형1, 변형2"
              className="h-64 w-full resize-y rounded-xl border border-line bg-ink-800/60 p-3 font-mono text-sm leading-relaxed text-white placeholder:text-muted/60 focus:border-accent/50 focus:outline-none"
            />
          )}

          <div className="mt-3 flex items-center justify-between">
            <span className="text-xs text-muted">{groups.length}개 그룹 인식됨</span>
            <button
              type="button"
              onClick={save}
              disabled={saving || loading}
              className="rounded-xl bg-accent px-5 py-2.5 text-sm font-semibold text-ink-950 transition-all hover:bg-accent-soft disabled:opacity-50"
            >
              {saving ? "저장 중…" : "저장"}
            </button>
          </div>

          {msg && (
            <div
              className={
                "mt-3 rounded-lg px-3 py-2 text-sm " +
                (msg.kind === "ok"
                  ? "border border-pos/30 bg-pos/10 text-pos"
                  : "border border-neg/30 bg-neg/10 text-neg")
              }
            >
              {msg.text}
            </div>
          )}
        </CardBody>
      </Card>

      <p className="text-xs text-muted/70">
        ⓘ 별칭은 팀 전체에 공유되며, <b>저장 후 파일을 다시 업로드</b>하면 병합된 결과가 반영됩니다.
      </p>
    </div>
  );
}
