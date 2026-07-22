"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

interface NavItem {
  href: string;
  label: string;
  icon: JSX.Element;
}

const icon = (path: string) => (
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

const NAV: NavItem[] = [
  { href: "/", label: "Dashboard", icon: icon("M3 13h8V3H3v10Zm0 8h8v-6H3v6Zm10 0h8V11h-8v10Zm0-18v6h8V3h-8Z") },
  { href: "/menu", label: "메뉴 분석", icon: icon("M4 6h16M4 12h16M4 18h10") },
  { href: "/stores", label: "가맹점 분석", icon: icon("M3 21h18M5 21V7l7-4 7 4v14M9 21v-6h6v6") },
  { href: "/report", label: "AI Report", icon: icon("M9 12h6m-6 4h6M9 8h6M6 3h9l3 3v15H6z") },
  { href: "/external", label: "외부요인", icon: icon("M12 3a9 9 0 1 0 9 9M12 3v9l6 3M12 3a9 9 0 0 1 9 9") },
  { href: "/settings", label: "설정", icon: icon("M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-2.7 1.1V21a2 2 0 1 1-4 0v-.1A1.6 1.6 0 0 0 7 19.4a1.6 1.6 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0-1.1-2.7H1a2 2 0 1 1 0-4h.1A1.6 1.6 0 0 0 2.6 7") },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="fixed inset-y-0 left-0 z-30 flex w-60 flex-col border-r border-line bg-ink-900/80 backdrop-blur-xl">
      <div className="flex items-center gap-2.5 px-5 py-6">
        <div className="grid h-9 w-9 place-items-center rounded-xl bg-accent/15 ring-1 ring-accent/30">
          <span className="text-accent text-lg font-bold">M</span>
        </div>
        <div className="leading-tight">
          <div className="text-sm font-semibold text-white">Menu Intelligence</div>
          <div className="text-[11px] tracking-wide text-muted">AI Analytics</div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3">
        {NAV.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
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

      <div className="px-5 py-5 text-[11px] leading-relaxed text-muted/70">
        생전포차 체인 · POS 기반<br />메뉴 성장/감소 자동 분석
      </div>
    </aside>
  );
}
