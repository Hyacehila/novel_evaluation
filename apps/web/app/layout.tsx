import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

import { AppShell } from "@/shared/layouts/app-shell";
import { QueryProvider } from "@/shared/providers/query-provider";


export const metadata: Metadata = {
  title: "小说智能打分系统",
  description: "基于 LLM rubric 的小说结构化评价工作台",
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
