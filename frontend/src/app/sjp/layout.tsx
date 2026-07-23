"use client";

import { Sidebar, navIcon, type NavItem } from "@/components/layout/Sidebar";

const ITEMS: NavItem[] = [
  { href: "/sjp", label: "Dashboard", icon: navIcon("M3 13h8V3H3v10Zm0 8h8v-6H3v6Zm10 0h8V11h-8v10Zm0-18v6h8V3h-8Z") },
  { href: "/sjp/menu", label: "메뉴 분석", icon: navIcon("M4 6h16M4 12h16M4 18h10") },
  { href: "/sjp/stores", label: "가맹점 분석", icon: navIcon("M3 21h18M5 21V7l7-4 7 4v14M9 21v-6h6v6") },
  { href: "/sjp/report", label: "AI Report", icon: navIcon("M9 12h6m-6 4h6M9 8h6M6 3h9l3 3v15H6z") },
  { href: "/sjp/external", label: "외부요인", icon: navIcon("M12 3a9 9 0 1 0 9 9M12 3v9l6 3M12 3a9 9 0 0 1 9 9") },
  { href: "/sjp/settings", label: "설정", icon: navIcon("M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-2.7 1.1V21a2 2 0 1 1-4 0v-.1A1.6 1.6 0 0 0 7 19.4a1.6 1.6 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0-1.1-2.7H1a2 2 0 1 1 0-4h.1A1.6 1.6 0 0 0 2.6 7") },
];

export default function SJPLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Sidebar items={ITEMS} brandName="생전포차" brandTag="Menu Analytics" homeHref="/sjp" />
      <main className="ml-60 min-h-screen px-8 pb-16 pt-0">{children}</main>
    </>
  );
}
