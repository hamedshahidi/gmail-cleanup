import { NextRequest } from "next/server";

import { proxyToFastApi } from "../_proxy";

export async function POST(request: NextRequest) {
  return proxyToFastApi(request, "/logout");
}
