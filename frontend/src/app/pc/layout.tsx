"use client";

import { Sidebar, navIcon, type NavItem } from "@/components/layout/Sidebar";

const ITEMS: NavItem[] = [
  { href: "/pc", label: "Dashboard", icon: navIcon("M3 13h8V3H3v10Zm0 8h8v-6H3v6Zm10 0h8V11h-8v10Zm0-18v6h8V3h-8Z") },
  { href: "/pc/products", label: "상품 분석", icon: navIcon("M4 6h16M4 12h16M4 18h10") },
  { href: "/pc/categories", label: "분류 분석", icon: navIcon("M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z") },
  { href: "/pc/report", label: "AI Report", icon: navIcon("M9 12h6m-6 4h6M9 8h6M6 3h9l3 3v15H6z") },
  { href: "/pc/aliases", label: "별칭 설정", icon: navIcon("M20.6 13.4 12 22l-9-9V3h10l7.6 7.6a2 2 0 0 1 0 2.8ZM7 7h.01") },
];

export default function PCLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Sidebar items={ITEMS} brandName="피씨 (PC방)" brandTag="Product Analytics" homeHref="/pc" />
      <main className="ml-60 min-h-screen px-8 pb-16 pt-0">{children}</main>
    </>
  );
}
