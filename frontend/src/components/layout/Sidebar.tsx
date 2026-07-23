"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export interface NavItem {
  href: string;
  label: string;
  icon: JSX.Element;
}

export const navIcon = (path: string) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.7"
    strokeLinecap="round"
    strokeLinejoin="round"
    className="h-[18px] w-[18px]"
  >
    <path d={path} />
  </svg>
);

export function Sidebar({
  items,
  brandName,
  brandTag,
  homeHref,
}: {
  items: NavItem[];
  brandName: string;
  brandTag: string;
  homeHref: string; // 브랜드 대시보드 루트 (활성 판정 기준)
}) {
  const pathname = usePathname();
  return (
    <aside className="fixed inset-y-0 left-0 z-30 flex w-60 flex-col border-r border-line bg-ink-900/80 backdrop-blur-xl">
      <div className="flex items-center gap-2.5 px-5 py-6">
        <div className="grid h-9 w-9 place-items-center rounded-xl bg-accent/15 ring-1 ring-accent/30">
          <span className="text-accent text-lg font-bold">M</span>
        </div>
        <div className="leading-tight">
          <div className="text-sm font-semibold text-white">{brandName}</div>
          <div className="text-[11px] tracking-wide text-muted">{brandTag}</div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3">
        {items.map((item) => {
          const active =
            item.href === homeHref
              ? pathname === homeHref
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all",
                active
                  ? "bg-accent/10 text-white ring-1 ring-inset ring-accent/25"
                  : "text-muted hover:bg-white/[0.04] hover:text-white/90",
              )}
            >
              <span className={active ? "text-accent" : "text-muted group-hover:text-white/80"}>
                {item.icon}
              </span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="px-3 pb-5">
        <Link
          href="/"
          className="flex items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium text-muted transition-colors hover:bg-white/[0.04] hover:text-white/90"
        >
          {navIcon("M9 5l-7 7 7 7M2 12h20")}
          브랜드 변경
        </Link>
      </div>
    </aside>
  );
}
