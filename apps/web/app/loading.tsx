export default function RootLoading() {
  return (
    <div className="page-frame">
      <div className="grain-card rounded-[28px] border border-[var(--line)] bg-[var(--surface)] p-10 shadow-[var(--shadow)]">
        <p className="text-sm uppercase tracking-[0.22em] text-[var(--muted)]">Loading</p>
        <h1 className="section-title mt-3 text-3xl font-semibold">正在装载工作台</h1>
        <p className="mt-4 max-w-2xl text-sm text-[var(--muted)]">
          页面正在读取当前任务、结果和历史摘要。
        </p>
      </div>
    </div>
  );
}
