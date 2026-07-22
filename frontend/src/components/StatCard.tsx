import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/utils";
import { pct, deltaClass } from "@/lib/format";

export function StatCard({
  label,
  value,
  delta,
  hint,
  accent = false,
}: {
  label: string;
  value: string;
  delta?: number | null;
  hint?: string;
  accent?: boolean;
}) {
  return (
    <Card className={cn("relative overflow-hidden", accent && "shadow-glow")}>
      <div className="card-pad">
        <div className="stat-label">{label}</div>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="text-[26px] font-semibold leading-none tracking-tight text-white">
            {value}
          </span>
          {delta != null && (
            <span className={cn("text-sm font-semibold", deltaClass(delta))}>
              {delta > 0 ? "▲" : delta < 0 ? "▼" : "–"} {pct(delta, false)}
            </span>
          )}
        </div>
        {hint && <div className="mt-1.5 text-xs text-muted">{hint}</div>}
      </div>
      {accent && (
        <div className="pointer-events-none absolute -right-8 -top-8 h-24 w-24 rounded-full bg-accent/20 blur-2xl" />
      )}
    </Card>
  );
}
