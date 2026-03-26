import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

import { AppShell } from "@/shared/layouts/app-shell";
import { QueryProvider } from "@/shared/providers/query-provider";


export const metadata: Metadata = {
  title: "小说评测工作台",
  description: "Novel evaluation delivery-ready workspace",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <QueryProvider>
          <AppShell>{children}</AppShell>
        </QueryProvider>
      </body>
    </html>
  );
}
