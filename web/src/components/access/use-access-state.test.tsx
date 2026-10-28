import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { accessRequest } from "@/components/access/access-api";
import { useAccessState } from "@/components/access/use-access-state";
import type { AccessState } from "@/types/access";

vi.mock("@/components/access/access-api", () => ({ accessRequest: vi.fn() }));
const request = vi.mocked(accessRequest);
const state: AccessState = { network: null, relay: { configured: false, available: false, running: false, public_host: null, reason_code: "relay_not_configured" }, services: [], poll_interval_seconds: 30 };

afterEach(() => { cleanup(); vi.resetAllMocks(); });

describe("public service polling", () => {
  it("preserves the last successful state and exposes a refresh error", async () => {
    request.mockResolvedValueOnce(state).mockRejectedValueOnce(new Error("Network offline"));
    const { result } = renderHook(useAccessState);
    await waitFor(() => expect(result.current.data).toEqual(state));
    await act(() => result.current.reload());
    expect(result.current.data).toEqual(state);
    expect(result.current.error).toBe("Network offline");
  });

  it("aborts the pending request when leaving the page", () => {
    request.mockReturnValue(new Promise(() => { }));
    const { unmount } = renderHook(useAccessState);
    const signal = request.mock.calls[0][1]?.signal;
    unmount();
    expect(signal?.aborted).toBe(true);
  });
});
