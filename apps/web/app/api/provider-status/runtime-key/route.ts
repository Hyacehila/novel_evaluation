import {
  buildForbiddenResponse,
  buildJsonProxyResponse,
  buildUpstreamUnavailableResponse,
  isLocalWebRequest,
} from "@/api/provider-route";

const apiHost = process.env.NOVEL_EVAL_API_HOST ?? "127.0.0.1";
const apiPort = process.env.NOVEL_EVAL_API_PORT ?? "8000";
const apiOrigin = `http://${apiHost}:${apiPort}`;

export async function POST(request: Request) {
  if (!isLocalWebRequest(request)) {
    return buildForbiddenResponse("仅允许本机通过 Web 界面录入运行时 Key。");
  }

  try {
    const body = await request.text();
    const response = await fetch(`${apiOrigin}/api/provider-status/runtime-key`, {
      method: "POST",
      headers: {
        "content-type": request.headers.get("content-type") ?? "application/json",
      },
      body,
      cache: "no-store",
    });
    const responseBody = await response.text();
    return buildJsonProxyResponse(responseBody, response.status, response.headers.get("content-type"));
  } catch {
    return buildUpstreamUnavailableResponse("当前无法连接 API 服务，请稍后重试。");
  }
}
