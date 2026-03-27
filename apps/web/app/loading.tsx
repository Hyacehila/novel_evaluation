export default function RootLoading() {
  return (
    <div className="page-frame">
      <div className="grain-card rounded-[28px] border border-[var(--line)] bg-[var(--surface)] p-10 shadow-[var(--shadow)]">
        <p className="text-sm tracking-[0.12em] text-[var(--muted)]">加载中</p>
        <h1 className="section-title mt-3 text-3xl font-semibold">正在加载工作台首页</h1>
        <p className="mt-4 max-w-2xl text-sm text-[var(--muted)]">
          正在读取评测任务、结果摘要与历史记录。
        </p>
      </div>
    </div>
  );
}
