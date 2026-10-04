import type { components } from "../generated/api";

export type Problem = components["schemas"]["Problem"];
export type Capabilities = components["schemas"]["Capabilities"];
export type Decoder<T> = (value: unknown) => T;
export type HttpTransport = (request: Request) => Promise<Response>;
export type ApiPath = `/api/v1/${string}`;

export class ApiError extends Error {
  readonly problem: Problem | null;
  readonly requestId: string;
  readonly status: number | null;
  readonly kind: "problem" | "network" | "timeout" | "invalid-response";

  constructor(
    kind: ApiError["kind"],
    message: string,
    requestId: string,
    status: number | null = null,
    problem: Problem | null = null,
  ) {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
    this.requestId = requestId;
    this.status = status;
    this.problem = problem;
  }
}

export class ContractError extends Error {
  constructor() {
    super("The response did not match the application contract.");
    this.name = "ContractError";
  }
}

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requestId(value: unknown): value is string {
  return typeof value === "string" && /^[A-Za-z0-9._-]{1,64}$/.test(value);
}

function isProblem(value: unknown): value is Problem {
  return (
    object(value) &&
    typeof value.type === "string" &&
    /^urn:benefitbridge:problem:[a-z0-9-]+$/.test(value.type) &&
    typeof value.title === "string" &&
    value.title.length > 0 &&
    typeof value.detail === "string" &&
    value.detail.length > 0 &&
    typeof value.code === "string" &&
    /^[A-Z][A-Z0-9_]*$/.test(value.code) &&
    typeof value.status === "number" &&
    Number.isInteger(value.status) &&
    value.status >= 400 &&
    value.status <= 599 &&
    requestId(value.request_id) &&
    typeof value.retryable === "boolean" &&
    Array.isArray(value.errors) &&
    value.errors.every(
      (error: unknown) =>
        object(error) &&
        typeof error.path === "string" &&
        typeof error.message === "string",
    )
  );
}

export function decodeCapabilities(value: unknown): Capabilities {
  if (
    !object(value) ||
    value.api_version !== "1" ||
    typeof value.watch !== "boolean" ||
    typeof value.demo_reset !== "boolean" ||
    typeof value.inference_available !== "boolean" ||
    typeof value.deep_available !== "boolean" ||
    typeof value.max_document_bytes !== "number" ||
    !Number.isSafeInteger(value.max_document_bytes) ||
    value.max_document_bytes <= 0 ||
    typeof value.max_document_pages !== "number" ||
    !Number.isSafeInteger(value.max_document_pages) ||
    value.max_document_pages <= 0 ||
    !Array.isArray(value.supported_lanes) ||
    new Set(value.supported_lanes).size !== value.supported_lanes.length ||
    !value.supported_lanes.every(
      (lane: unknown) =>
        lane === "INTERNSHIP_RESEARCH" || lane === "SCHOLARSHIP_PROGRAM",
    ) ||
    !Array.isArray(value.supported_document_types) ||
    !value.supported_document_types.every(
      (kind: unknown) => kind === "application/pdf",
    )
  ) {
    throw new ContractError();
  }
  return value as Capabilities;
}

export interface ApiClient {
  get<T>(path: ApiPath, decode: Decoder<T>, signal?: AbortSignal): Promise<T>;
}

export interface ApiClientOptions {
  origin: string;
  environment?: "production" | "development" | "test";
  getAccessToken?: () => string | null;
  transport?: HttpTransport;
  newRequestId?: () => string;
  timeoutMs?: number;
}

export function createApiClient(options: ApiClientOptions): ApiClient {
  const environment = options.environment ?? "production";
  if (options.transport && environment === "production") {
    throw new Error("Mock transports are restricted to tests and development.");
  }
  const origin = new URL(options.origin);
  if (
    origin.pathname !== "/" ||
    origin.search ||
    origin.hash ||
    origin.username ||
    origin.password
  ) {
    throw new Error(
      "The API origin must not contain a path, query or credentials.",
    );
  }
  if (
    origin.protocol !== "https:" &&
    !(
      environment !== "production" &&
      origin.protocol === "http:" &&
      ["localhost", "127.0.0.1", "[::1]"].includes(origin.hostname)
    )
  ) {
    throw new Error("The API requires HTTPS, except local development.");
  }
  const timeoutMs = options.timeoutMs ?? 15_000;
  if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) {
    throw new Error("Requests require a positive finite timeout.");
  }
  const transport: HttpTransport =
    options.transport ?? ((request) => fetch(request));
  const newRequestId = options.newRequestId ?? (() => crypto.randomUUID());

  return {
    async get<T>(
      path: ApiPath,
      decode: Decoder<T>,
      signal?: AbortSignal,
    ): Promise<T> {
      const url = new URL(path, origin);
      if (
        url.origin !== origin.origin ||
        !url.pathname.startsWith("/api/v1/") ||
        url.hash
      ) {
        throw new Error(
          "Requests must remain on the configured API origin and prefix.",
        );
      }
      const id = newRequestId();
      if (!requestId(id)) throw new Error("Invalid request ID.");
      const timeout = AbortSignal.timeout(timeoutMs);
      const combined = signal ? AbortSignal.any([signal, timeout]) : timeout;
      const headers = new Headers({
        Accept: "application/json, application/problem+json",
        "X-Request-ID": id,
      });
      const token = options.getAccessToken?.();
      if (token) headers.set("Authorization", `Bearer ${token}`);
      let response: Response;
      try {
        response = await transport(
          new Request(url, {
            method: "GET",
            headers,
            signal: combined,
            credentials: "omit",
            cache: "no-store",
            redirect: "error",
          }),
        );
      } catch (error: unknown) {
        if (signal?.aborted)
          throw new DOMException("Browser request cancelled.", "AbortError");
        if (timeout.aborted)
          throw new ApiError(
            "timeout",
            "The request timed out. Try again.",
            id,
          );
        if (error instanceof TypeError) {
          throw new ApiError(
            "network",
            "Could not connect. Check your connection and try again.",
            id,
          );
        }
        throw error;
      }
      const returnedId = response.headers.get("X-Request-ID");
      const safeId = requestId(returnedId) ? returnedId : id;
      const mediaType = response.headers
        .get("Content-Type")
        ?.split(";", 1)[0]
        ?.trim();
      if (
        mediaType !== "application/json" &&
        mediaType !== "application/problem+json"
      ) {
        throw new ApiError(
          "invalid-response",
          "The service returned an unexpected response. Try again.",
          safeId,
          response.status,
        );
      }
      let payload: unknown;
      try {
        payload = await response.json();
      } catch (error: unknown) {
        if (signal?.aborted)
          throw new DOMException("Browser request cancelled.", "AbortError");
        if (timeout.aborted)
          throw new ApiError(
            "timeout",
            "The request timed out. Try again.",
            safeId,
          );
        if (error instanceof TypeError)
          throw new ApiError(
            "network",
            "The connection was interrupted. Try again.",
            safeId,
          );
        if (!(error instanceof SyntaxError)) throw error;
        throw new ApiError(
          "invalid-response",
          "The service returned an unreadable response. Try again.",
          safeId,
          response.status,
        );
      }
      if (signal?.aborted)
        throw new DOMException("Browser request cancelled.", "AbortError");
      if (timeout.aborted)
        throw new ApiError(
          "timeout",
          "The request timed out. Try again.",
          safeId,
        );
      if (!response.ok) {
        if (
          mediaType === "application/problem+json" &&
          isProblem(payload) &&
          payload.status === response.status
        ) {
          throw new ApiError(
            "problem",
            payload.detail,
            payload.request_id,
            response.status,
            payload,
          );
        }
        throw new ApiError(
          "invalid-response",
          "The service could not complete this request. Try again.",
          safeId,
          response.status,
        );
      }
      if (
        !object(payload) ||
        !requestId(payload.request_id) ||
        !("data" in payload)
      ) {
        throw new ApiError(
          "invalid-response",
          "The service returned an incomplete response. Try again.",
          safeId,
          response.status,
        );
      }
      try {
        return decode(payload.data);
      } catch (error: unknown) {
        if (!(error instanceof ContractError)) throw error;
        throw new ApiError(
          "invalid-response",
          error.message,
          payload.request_id,
          response.status,
        );
      }
    },
  };
}
