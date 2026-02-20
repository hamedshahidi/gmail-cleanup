import { NextRequest, NextResponse } from "next/server";

const DEFAULT_FASTAPI_BASE_URL = "http://127.0.0.1:8000";

function fastApiBaseUrl(): string {
  return process.env.FASTAPI_BASE_URL || DEFAULT_FASTAPI_BASE_URL;
}

function buildForwardHeaders(request: NextRequest): Headers {
  const headers = new Headers();

  for (const [key, value] of request.headers.entries()) {
    const lowerKey = key.toLowerCase();
    if (lowerKey === "host" || lowerKey === "content-length") {
      continue;
    }
    headers.set(key, value);
  }

  const cookie = request.headers.get("cookie");
  if (cookie) {
    headers.set("cookie", cookie);
  }

  return headers;
}

function copySetCookieHeaders(source: Headers, target: Headers): void {
  const withGetSetCookie = source as Headers & { getSetCookie?: () => string[] };
  const setCookies = withGetSetCookie.getSetCookie?.() ?? [];

  if (setCookies.length > 0) {
    for (const cookie of setCookies) {
      target.append("set-cookie", cookie);
    }
    return;
  }

  const setCookie = source.get("set-cookie");
  if (setCookie) {
    target.append("set-cookie", setCookie);
  }
}

export async function proxyToFastApi(
  request: NextRequest,
  upstreamPath: string,
): Promise<NextResponse> {
  const url = new URL(upstreamPath, fastApiBaseUrl());
  const headers = buildForwardHeaders(request);
  const bodyText = request.method === "GET" || request.method === "HEAD" ? "" : await request.text();
  const upstreamResponse = await fetch(url, {
    method: request.method,
    headers,
    body: bodyText ? bodyText : undefined,
    redirect: "manual",
    cache: "no-store",
  });

  const responseHeaders = new Headers();
  for (const [key, value] of upstreamResponse.headers.entries()) {
    if (key.toLowerCase() === "set-cookie") {
      continue;
    }
    responseHeaders.set(key, value);
  }
  copySetCookieHeaders(upstreamResponse.headers, responseHeaders);

  return new NextResponse(upstreamResponse.body, {
    status: upstreamResponse.status,
    statusText: upstreamResponse.statusText,
    headers: responseHeaders,
  });
}
