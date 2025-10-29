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
}

export class ApiClientError extends Error {
  constructor(message: string, readonly status: number, readonly data?: unknown) {
    super(message);
    this.name = "ApiClientError";
  }
}

const DEFAULT_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8003";

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

export async function apiClient<TResponse = unknown, TBody = unknown>(
  endpoint: string,
  { body, headers, parseAs = "json", ...init }: ApiClientOptions<TBody> = {},
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

  const response = await fetch(resolveUrl(endpoint), {
    ...init,
    headers: requestHeaders,
    body: requestBody,
  });

  if (!response.ok) {
    const payload = await parseErrorPayload(response);
    const message =
      (payload && typeof payload === "object" && "message" in payload && typeof payload.message === "string"
        ? payload.message
        : typeof payload === "string"
          ? payload
          : `Request failed with status ${response.status}`) ?? `Request failed with status ${response.status}`;

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
