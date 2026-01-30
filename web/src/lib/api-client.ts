export type ResponseParser = "json" | "text" | "response";

export interface ApiClientOptions<TBody = unknown> extends Omit<RequestInit, "body"> {
  /**
   * Request body. Objects are serialized as JSON by default.
   */
  body?: TBody;
  /**
   * How the response should be parsed. Defaults to `"json"`.
   */
  parseAs?: ResponseParser;
  /**
   * Whether to include the stored bearer token automatically.
   * Defaults to `true`.
   */
  includeAuth?: boolean;
}

export class ApiClientError extends Error {
  constructor(message: string, readonly status: number, readonly data?: unknown) {
    super(message);
    this.name = "ApiClientError";
  }
}

const DEFAULT_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8003";

let authToken: string | null = null;
type UnauthorizedHandler = () => void;

let unauthorizedHandler: UnauthorizedHandler | null = null;

export function setAuthToken(token: string | null): void {
  authToken = token;
}

export function getAuthToken(): string | null {
  return authToken;
}

export function setUnauthorizedHandler(handler: UnauthorizedHandler | null): void {
  unauthorizedHandler = handler;
}

export interface ApiEnvelope<T> {
  code: number;
  message?: string;
  data?: T;
}

export function isApiEnvelope<T>(value: unknown): value is ApiEnvelope<T> {
  return typeof value === "object" && value !== null && "code" in value;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function getErrorMessage(error: unknown, fallback = "Unexpected error"): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return fallback;
}

function resolveUrl(endpoint: string): string {
  if (endpoint.startsWith("http://") || endpoint.startsWith("https://")) {
    return endpoint;
  }

  const normalized = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  return `${DEFAULT_BASE_URL}${normalized}`;
}

async function parseErrorPayload(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type");

  if (contentType?.includes("application/json")) {
    try {
      return await response.json();
    } catch {
      return undefined;
    }
  }

  try {
    const text = await response.text();
    return text || undefined;
  } catch {
    return undefined;
  }
}

function extractErrorMessage(payload: unknown): string | undefined {
  if (typeof payload === "string") {
    return payload;
  }

  if (!isRecord(payload)) {
    return undefined;
  }

  if (typeof payload.message === "string") {
    return payload.message;
  }

  const detail = payload.detail;
  if (typeof detail === "string") {
    return detail;
  }

  if (isRecord(detail) && typeof detail.message === "string") {
    return detail.message;
  }

  if (Array.isArray(detail)) {
    const first = detail.find((item) => isRecord(item) && typeof item.msg === "string");
    if (first && isRecord(first) && typeof first.msg === "string") {
      return first.msg;
    }
  }

  return undefined;
}

export async function apiClient<TResponse = unknown, TBody = unknown>(
  endpoint: string,
  { body, headers, parseAs = "json", includeAuth = true, ...init }: ApiClientOptions<TBody> = {},
): Promise<TResponse> {
  const requestHeaders = new Headers(headers);
  let requestBody: BodyInit | undefined;

  if (body instanceof FormData || body instanceof URLSearchParams || body instanceof Blob) {
    requestBody = body;
  } else if (typeof body === "string") {
    requestBody = body;
    if (!requestHeaders.has("Content-Type")) {
      requestHeaders.set("Content-Type", "text/plain;charset=UTF-8");
    }
  } else if (body !== undefined) {
    requestHeaders.set("Content-Type", "application/json");
    requestBody = JSON.stringify(body);
  }

  if (includeAuth && authToken && !requestHeaders.has("Authorization")) {
    requestHeaders.set("Authorization", `Bearer ${authToken}`);
  }

  const response = await fetch(resolveUrl(endpoint), {
    ...init,
    headers: requestHeaders,
    body: requestBody,
  });

  if (!response.ok) {
    const payload = await parseErrorPayload(response);
    const message = extractErrorMessage(payload) ?? `Request failed with status ${response.status}`;

    if (response.status === 401 && unauthorizedHandler) {
      unauthorizedHandler();
    }

    throw new ApiClientError(message, response.status, payload);
  }

  switch (parseAs) {
    case "response":
      return response as unknown as TResponse;
    case "text":
      return (await response.text()) as unknown as TResponse;
    default: {
      if (response.status === 204) {
        return undefined as TResponse;
      }
      const contentType = response.headers.get("content-type");
      if (!contentType?.includes("application/json")) {
        return undefined as TResponse;
      }
      if (response.headers.get("content-length") === "0") {
        return undefined as TResponse;
      }
      return (await response.json()) as TResponse;
    }
  }
}
