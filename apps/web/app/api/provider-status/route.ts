import { buildJsonProxyResponse, buildUpstreamUnavailableResponse } from "@/api/provider-route";

const apiHost = process.env.NOVEL_EVAL_API_HOST ?? "127.0.0.1";
const apiPort = process.env.NOVEL_EVAL_API_PORT ?? "8000";
const apiOrigin = `http://${apiHost}:${apiPort}`;

export async function GET() {
  try {
    const response = await fetch(`${apiOrigin}/api/provider-status`, {
      cache: "no-store",
    });
    const body = await response.text();
    return buildJsonProxyResponse(body, response.status, response.headers.get("content-type"));
  } catch {
    return buildUpstreamUnavailableResponse("当前无法连接 API 服务，请稍后重试。");
  }
}
