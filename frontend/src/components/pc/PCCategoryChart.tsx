"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { PCCategorySales } from "@/types/pc";
import { won, wonShort } from "@/lib/format";

const AXIS = { fill: "#8ba0bd", fontSize: 11 };

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-line bg-ink-850 px-3 py-2 text-xs shadow-card">
      <div className="mb-1 font-semibold text-white">{label}</div>
      {payload.map((p: any) => (
        <div key={p.dataKey} className="flex items-center gap-2 text-white/80">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: p.color }} />
          {p.name}: {won(p.value)}
        </div>
      ))}
    </div>
  );
}

/** 분류별 당월/전월 매출 비교 (가로 막대). */
export function PCCategoryChart({ data }: { data: PCCategorySales[] }) {
  const rows = data.slice(0, 12);
  return (
    <ResponsiveContainer width="100%" height={Math.max(280, rows.length * 32)}>
      <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 16, top: 4, bottom: 4 }}>
        <CartesianGrid horizontal={false} stroke="#1b2433" />
        <XAxis type="number" tick={AXIS} tickFormatter={(v) => wonShort(v)} axisLine={false} tickLine={false} />
        <YAxis type="category" dataKey="name" tick={AXIS} width={92} axisLine={false} tickLine={false} />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
        <Bar dataKey="prev" name="전월" fill="#374151" radius={[0, 4, 4, 0]} barSize={9} />
        <Bar dataKey="curr" name="당월" fill="#e5b567" radius={[0, 4, 4, 0]} barSize={9} />
      </BarChart>
    </ResponsiveContainer>
  );
}
