import type { components } from "../src/generated/api";
import type { HttpTransport } from "../src/lib/api";

export const syntheticCapabilities: components["schemas"]["Capabilities"] = {
  api_version: "1",
  watch: false,
  demo_reset: false,
  inference_available: false,
  deep_available: false,
  max_document_bytes: 1024,
  max_document_pages: 1,
  supported_lanes: ["SCHOLARSHIP_PROGRAM"],
  supported_document_types: ["application/pdf"],
};

// Test-only adapter: the application entrypoint never imports this module.
export const mockTransport: HttpTransport = async (request) => {
  request.signal.throwIfAborted();
  if (
    request.method !== "GET" ||
    new URL(request.url).pathname !== "/api/v1/capabilities"
  ) {
    throw new Error("No synthetic response registered for this request.");
  }
  return new Response(
    JSON.stringify({
      data: syntheticCapabilities,
      request_id: "synthetic-response",
    }),
    {
      headers: {
        "Content-Type": "application/json",
        "X-Request-ID": "synthetic-response",
      },
    },
  );
};
