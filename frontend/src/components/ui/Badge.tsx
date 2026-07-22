import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

type Tone = "pos" | "neg" | "neutral" | "accent" | "gold";

const tones: Record<Tone, string> = {
  pos: "bg-pos/12 text-pos ring-1 ring-inset ring-pos/25",
  neg: "bg-neg/12 text-neg ring-1 ring-inset ring-neg/25",
  neutral: "bg-white/[0.06] text-muted ring-1 ring-inset ring-white/10",
  accent: "bg-accent/12 text-accent ring-1 ring-inset ring-accent/25",
  gold: "bg-gold/12 text-gold ring-1 ring-inset ring-gold/25",
};

export function Badge({
  children,
  tone = "neutral",
  className,
}: {
  children: ReactNode;
  tone?: Tone;
  className?: string;
}) {
  return <span className={cn("chip", tones[tone], className)}>{children}</span>;
}
