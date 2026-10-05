import assert from "node:assert/strict";
import test from "node:test";
import { mockTransport, syntheticCapabilities } from "./mockTransport.ts";
import {
  ApiError,
  ContractError,
  createApiClient,
  decodeCapabilities,
} from "../src/lib/api.ts";

const capabilities = Object.freeze({
  api_version: "1",
  watch: false,
  demo_reset: false,
  inference_available: false,
  deep_available: false,
  max_document_bytes: 1024,
  max_document_pages: 1,
  supported_lanes: ["SCHOLARSHIP_PROGRAM"],
  supported_document_types: ["application/pdf"],
});
const problem = Object.freeze({
  type: "urn:benefitbridge:problem:validation-error",
  title: "Invalid input",
  detail: "<script>unsafe()</script>",
  status: 422,
  code: "VALIDATION_ERROR",
  request_id: "synthetic-problem",
  errors: [{ path: "goal", message: "A goal is required" }],
  retryable: false,
});
function response(data, status = 200, contentType = "application/json") {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": contentType,
      "X-Request-ID": "synthetic-response",
    },
  });
}
function client(transport, options = {}) {
  return createApiClient({
    origin: "https://synthetic.invalid",
    environment: "test",
    newRequestId: () => "synthetic-request",
    transport,
    ...options,
  });
}

test("the generated-type mock implements the same transport contract", async () => {
  assert.deepEqual(
    await client(mockTransport).get("/api/v1/capabilities", decodeCapabilities),
    syntheticCapabilities,
  );
});

test("typed success with bearer in headers, private caching and bounded same-origin requests", async () => {
  const api = client(
    async (request) => {
      assert.equal(
        request.url,
        "https://synthetic.invalid/api/v1/capabilities",
      );
      assert.equal(
        request.headers.get("Authorization"),
        "Bearer synthetic-token",
      );
      assert.equal(request.headers.get("X-Request-ID"), "synthetic-request");
      assert.equal(request.cache, "no-store");
      assert.equal(request.credentials, "omit");
      assert.equal(request.redirect, "error");
      return response({ data: capabilities, request_id: "synthetic-response" });
    },
    { getAccessToken: () => "synthetic-token" },
  );
  assert.deepEqual(
    await api.get("/api/v1/capabilities", decodeCapabilities),
    capabilities,
  );
  await assert.rejects(
    api.get("https://other.invalid/api/v1/capabilities", decodeCapabilities),
    /origin/,
  );
  await assert.rejects(
    api.get("/api/v1/../account", decodeCapabilities),
    /prefix/,
  );
});

test("production refuses mocks and insecure origins", () => {
  assert.throws(
    () =>
      createApiClient({
        origin: "https://synthetic.invalid",
        transport: async () => response({}),
      }),
    /restricted/,
  );
  assert.throws(() => createApiClient({ origin: "http://localhost" }), /HTTPS/);
  assert.throws(
    () =>
      client(async () => response({}), {
        origin: "https://synthetic.invalid/path",
      }),
    /origin/,
  );
});

test("consent PATCH uses the shared bearer transport and generated request shape", async () => {
  const consent = { consent_version: "2026-10-01" };
  const api = client(
    async (request) => {
      assert.equal(request.method, "PATCH");
      assert.equal(request.url, "https://synthetic.invalid/api/v1/me");
      assert.equal(
        request.headers.get("Authorization"),
        "Bearer synthetic-token",
      );
      assert.equal(request.headers.get("Content-Type"), "application/json");
      assert.equal(request.cache, "no-store");
      assert.deepEqual(await request.json(), consent);
      return response({ data: consent, request_id: "synthetic-response" });
    },
    { getAccessToken: () => "synthetic-token" },
  );
  assert.deepEqual(
    await api.patch("/api/v1/me", consent, (data) => data),
    consent,
  );
});

test("a current bearer 401 ends the session even when its body is invalid", async () => {
  let token = "synthetic-token";
  let expired = 0;
  const api = client(async () => new Response("unreadable", { status: 401 }), {
    getAccessToken: () => token,
    onUnauthorized: () => {
      token = null;
      expired++;
    },
  });
  await assert.rejects(
    api.get("/api/v1/me", (data) => data),
    ApiError,
  );
  assert.equal(expired, 1);
  assert.equal(token, null);
});

test("an old bearer 401 cannot end a newer session", async () => {
  let token = "old-synthetic-token";
  let expired = 0;
  const api = client(
    async () => {
      token = "new-synthetic-token";
      return response({}, 401);
    },
    {
      getAccessToken: () => token,
      onUnauthorized: () => expired++,
    },
  );
  await assert.rejects(
    api.get("/api/v1/me", (data) => data),
    ApiError,
  );
  assert.equal(expired, 0);
  assert.equal(token, "new-synthetic-token");
});

test("structured problems preserve field errors and safe request reference", async () => {
  await assert.rejects(
    client(async () => response(problem, 422, "application/problem+json")).get(
      "/api/v1/capabilities",
      decodeCapabilities,
    ),
    (error) => {
      assert.ok(error instanceof ApiError);
      assert.equal(error.problem.code, "VALIDATION_ERROR");
      assert.equal(error.requestId, "synthetic-problem");
      assert.equal(error.message, problem.detail);
      return true;
    },
  );
});

test("unexpected HTML and malformed success are rejected without exposing response bodies", async () => {
  for (const result of [
    new Response("private synthetic content", {
      status: 502,
      headers: { "Content-Type": "text/html" },
    }),
    response({ data: capabilities }),
    response({
      data: { ...capabilities, max_document_pages: "one" },
      request_id: "synthetic-response",
    }),
  ]) {
    await assert.rejects(
      client(async () => result).get(
        "/api/v1/capabilities",
        decodeCapabilities,
      ),
      (error) =>
        error instanceof ApiError &&
        error.kind === "invalid-response" &&
        !error.message.includes("private"),
    );
  }
  assert.throws(
    () =>
      decodeCapabilities({ ...capabilities, supported_lanes: ["invented"] }),
    ContractError,
  );
});

test("network failures are visible without internal exception text", async () => {
  await assert.rejects(
    client(async () => {
      throw new TypeError("private transport detail");
    }).get("/api/v1/capabilities", decodeCapabilities),
    (error) =>
      error instanceof ApiError &&
      error.kind === "network" &&
      !error.message.includes("private"),
  );
});

function waiting(request) {
  return new Promise((resolve, reject) => {
    const keepAlive = setTimeout(
      () => reject(new Error("test transport did not abort")),
      1000,
    );
    request.signal.addEventListener(
      "abort",
      () => {
        clearTimeout(keepAlive);
        reject(request.signal.reason);
      },
      { once: true },
    );
    if (request.signal.aborted) {
      clearTimeout(keepAlive);
      reject(request.signal.reason);
    }
  });
}

test("browser cancellation aborts only its GET request", async () => {
  const controller = new AbortController();
  const api = client(async (request) => {
    assert.equal(request.method, "GET");
    controller.abort();
    return waiting(request);
  });
  await assert.rejects(
    api.get("/api/v1/capabilities", decodeCapabilities, controller.signal),
    { name: "AbortError" },
  );
});

test("request timeout stops the spinner with an explicit error", async () => {
  await assert.rejects(
    client(waiting, { timeoutMs: 10 }).get(
      "/api/v1/capabilities",
      decodeCapabilities,
    ),
    (error) => error instanceof ApiError && error.kind === "timeout",
  );
});

test("cancellation during body decoding cannot become a successful result", async () => {
  const controller = new AbortController();
  const api = client(async () => {
    const result = response({
      data: capabilities,
      request_id: "synthetic-response",
    });
    result.json = async () => {
      controller.abort();
      return { data: capabilities, request_id: "synthetic-response" };
    };
    return result;
  });
  await assert.rejects(
    api.get("/api/v1/capabilities", decodeCapabilities, controller.signal),
    { name: "AbortError" },
  );
});
