import { NextRequest } from "next/server";

import { proxyToFastApi } from "../_proxy";

export async function GET(request: NextRequest) {
  return proxyToFastApi(request, "/health");
}
