const LOCAL_HOSTS = new Set(["127.0.0.1", "localhost", "::1", "[::1]"]);

function normalizeHostName(hostname: string | null) {
  if (hostname === null) {
    return null;
  }
  const normalized = hostname.toLowerCase();
  if (normalized.startsWith("::ffff:")) {
    return normalized.slice("::ffff:".length);
  }
  return normalized;
}

function isLocalHostName(hostname: string | null) {
  const normalized = normalizeHostName(hostname);
  return normalized !== null && LOCAL_HOSTS.has(normalized);
}

function getHostnameFromUrl(value: string | null) {
  if (!value) {
    return null;
  }
  try {
    return new URL(value).hostname;
  } catch {
    return null;
  }
}

function splitHeaderValues(value: string | null) {
  return (value ?? "")
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
}

function normalizeForwardedToken(value: string) {
  const strippedValue = value.trim().replace(/^for=/i, "").replace(/^host=/i, "");
  const unquoted = strippedValue.replace(/^"|"$/g, "");
  const normalizedHost = normalizeHostName(unquoted);
  if (!normalizedHost || normalizedHost === "unknown") {
    return null;
  }
  if (normalizedHost.startsWith("[")) {
    const closingBracketIndex = normalizedHost.indexOf("]");
    if (closingBracketIndex === -1) {
      return normalizedHost;
    }
    return normalizeHostName(normalizedHost.slice(1, closingBracketIndex));
  }
  const segments = normalizedHost.split(":");
  if (segments.length === 2 && /^\d+$/.test(segments[1] ?? "")) {
    return normalizeHostName(segments[0] ?? null);
  }
  return normalizedHost;
}

function forwardedClientHosts(headers: Headers) {
  const forwardedForHosts = splitHeaderValues(headers.get("x-forwarded-for"))
    .map((value) => normalizeForwardedToken(value))
    .filter((value): value is string => value !== null);
  const realIp = normalizeForwardedToken(headers.get("x-real-ip") ?? "");
  const forwardedHosts = splitHeaderValues(headers.get("forwarded")).flatMap((value) => {
    return value
      .split(";")
      .map((segment) => segment.trim())
      .filter((segment) => segment.toLowerCase().startsWith("for="))
      .map((segment) => normalizeForwardedToken(segment))
      .filter((segment): segment is string => segment !== null);
  });

  return [...forwardedForHosts, ...(realIp ? [realIp] : []), ...forwardedHosts];
}

export function isLocalWebRequest(request: Request) {
  const requestHost = getHostnameFromUrl(request.url);
  if (!isLocalHostName(requestHost)) {
    return false;
  }

  const originHost = getHostnameFromUrl(request.headers.get("origin"));
  const refererHost = getHostnameFromUrl(request.headers.get("referer"));
  if (originHost === null && refererHost === null) {
    return false;
  }
  if (originHost !== null && !isLocalHostName(originHost)) {
    return false;
  }
  if (refererHost !== null && !isLocalHostName(refererHost)) {
    return false;
  }

  return forwardedClientHosts(request.headers).every((host) => isLocalHostName(host));
}

export function buildJsonProxyResponse(body: string, status: number, contentType: string | null) {
  return new Response(body, {
    status,
    headers: {
      "cache-control": "no-store",
      "content-type": contentType ?? "application/json",
    },
  });
}

export function buildUpstreamUnavailableResponse(message: string) {
  return Response.json(
    {
      success: false,
      error: {
        code: "UPSTREAM_UNAVAILABLE",
        message,
      },
    },
    {
      status: 503,
      headers: {
        "cache-control": "no-store",
      },
    }
  );
}

export function buildForbiddenResponse(message: string) {
  return Response.json(
    {
      success: false,
      error: {
        code: "FORBIDDEN",
        message,
      },
    },
    {
      status: 403,
      headers: {
        "cache-control": "no-store",
      },
    }
  );
}
