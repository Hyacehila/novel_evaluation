import { ResultDetailPage } from "@/features/result-detail/result-detail-page";


export default async function Page({
  params,
}: {
  params: Promise<{ taskId: string }>;
}) {
  const { taskId } = await params;
  return <ResultDetailPage taskId={taskId} />;
}
