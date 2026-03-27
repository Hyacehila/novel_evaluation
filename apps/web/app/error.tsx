"use client";

import { useEffect } from "react";

import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";


export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="page-frame">
      <Card className="grain-card p-10">
        <p className="text-sm tracking-[0.12em] text-[var(--bad)]">页面异常</p>
        <h1 className="section-title mt-3 text-3xl font-semibold">页面加载失败</h1>
        <p className="mt-4 max-w-2xl text-sm text-[var(--muted)]">
          当前页面出现未处理异常。可以重试当前视图，或返回工作台首页继续查看评测任务。
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Button onClick={reset}>重试当前页面</Button>
          <Button asLink href="/" variant="secondary">
            返回首页
          </Button>
        </div>
      </Card>
    </div>
  );
}
