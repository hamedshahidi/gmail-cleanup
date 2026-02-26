import { NextRequest } from "next/server";

import { proxyToFastApi } from "../../../_proxy";

type RouteContext = {
  params:
    | {
        id: string;
      }
    | Promise<{
        id: string;
      }>;
};

export async function GET(request: NextRequest, context: RouteContext) {
  const { id } = await context.params;
  return proxyToFastApi(request, `/accounts/${encodeURIComponent(id)}/messages`);
}
