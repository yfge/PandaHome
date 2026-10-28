import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { P2pManager } from "@/components/p2p/p2p-manager";
import { type P2pSnapshot } from "@/components/p2p/p2p-api";
import { setAuthToken } from "@/lib/api-client";

const snapshot: P2pSnapshot = {
  provider: { configured: true, available: true, running: true, reason_code: "p2p_awaiting_connection", connection_type: "unknown" },
  services: [{ id: 1, name: "Home app", local_ip: "192.168.1.5", local_port: 8080, enabled: true,
    fallback_enabled: true, status: "awaiting_connection", reason_code: "p2p_awaiting_connection", connection_type: "unknown" }],
};

function response(data: unknown, status = 200) {
  return new Response(JSON.stringify(status === 200 ? { code: 0, data } : { detail: data }), {
    status, headers: { "Content-Type": "application/json" },
  });
}

function mount(locale = "en") {
  return render(<NextIntlClientProvider locale={locale} messages={{}} timeZone="Asia/Shanghai"><P2pManager /></NextIntlClientProvider>);
}

describe("private P2P service management", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    fetchMock.mockImplementation(async () => response(snapshot));
    vi.stubGlobal("fetch", fetchMock);
    setAuthToken("admin-token");
  });
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    setAuthToken(null);
  });

  it("distinguishes a running process from verified NAT traversal", async () => {
    mount();
    expect(await screen.findByText("Home app")).toBeInTheDocument();
    expect(screen.getByText("Awaiting remote connection")).toBeInTheDocument();
    expect(screen.getByText(/A running agent does not confirm/)).toBeInTheDocument();
    expect(screen.getByText(/Connection path unverified/)).toBeInTheDocument();
    expect(screen.getByText("frpc -c visitor.toml")).toBeInTheDocument();
    const [, options] = fetchMock.mock.calls[0];
    expect(options.headers.get("Authorization")).toBe("Bearer admin-token");
  });

  it("keeps a failed load visible and allows retry", async () => {
    fetchMock.mockResolvedValueOnce(response("Coordinator unavailable", 502));
    const user = userEvent.setup();
    mount();
    expect(await screen.findByRole("alert")).toHaveTextContent("Coordinator unavailable");
    await user.click(screen.getByRole("button", { name: "Refresh" }));
    expect(await screen.findByText("Home app")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("reports an incomplete success envelope and recovers on refresh", async () => {
    fetchMock.mockResolvedValueOnce(response(undefined));
    const user = userEvent.setup();
    mount();
    expect(await screen.findByRole("alert")).toHaveTextContent("The private access request could not be completed.");
    expect(screen.queryByText("Home app")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Refresh" }));
    expect(await screen.findByText("Home app")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("saves only service fields when toggling enabled", async () => {
    const user = userEvent.setup();
    mount();
    await screen.findByText("Home app");
    await user.click(screen.getByRole("button", { name: "Disable" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    const [url, request] = fetchMock.mock.calls[1];
    expect(url).toMatch(/\/api\/p2p\/services\/1$/);
    expect(request.method).toBe("PUT");
    expect(JSON.parse(request.body)).toEqual({ name: "Home app", local_ip: "192.168.1.5", local_port: 8080, enabled: false, fallback_enabled: true });
  });

  it("limits new service names to the backend's 80-character boundary", async () => {
    const user = userEvent.setup();
    mount();
    await screen.findByText("Home app");
    await user.click(screen.getByRole("button", { name: "Add service" }));
    await user.type(screen.getByLabelText("Name"), "a".repeat(81));
    expect(screen.getByLabelText("Name")).toHaveValue("a".repeat(80));
    await user.click(screen.getByRole("button", { name: "Save service" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    const [url, request] = fetchMock.mock.calls[1];
    expect(url).toMatch(/\/api\/p2p\/services$/);
    expect(request.method).toBe("POST");
    expect(JSON.parse(request.body).name).toBe("a".repeat(80));
  });

  it("downloads the visitor file with auth and the chosen bind port", async () => {
    const createUrl = vi.fn(() => "blob:visitor");
    vi.stubGlobal("URL", class extends URL { static createObjectURL = createUrl; static revokeObjectURL = vi.fn(); });
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
    const user = userEvent.setup();
    mount();
    await screen.findByText("Home app");
    fireEvent.change(screen.getByLabelText("Remote local port"), { target: { value: "19090" } });
    fetchMock.mockResolvedValueOnce(new Response("secretKey = 'sensitive'", { headers: { "Content-Type": "application/toml" } }));
    await user.click(screen.getByRole("button", { name: "Download visitor configuration" }));
    await waitFor(() => expect(click).toHaveBeenCalledTimes(1));
    const [url, request] = fetchMock.mock.calls[1];
    expect(url).toMatch(/\/api\/p2p\/services\/1\/visitor\?bind_port=19090$/);
    expect(request.headers.get("Authorization")).toBe("Bearer admin-token");
    expect(request.cache).toBe("no-store");
    expect(createUrl).toHaveBeenCalledOnce();
    expect(screen.queryByText(/sensitive/)).not.toBeInTheDocument();
  });

  it("rejects invalid visitor ports and displays export errors", async () => {
    const user = userEvent.setup();
    mount();
    await screen.findByText("Home app");
    fireEvent.change(screen.getByLabelText("Remote local port"), { target: { value: "65536" } });
    expect(screen.getByRole("button", { name: "Download visitor configuration" })).toBeDisabled();
    expect(screen.getByRole("alert")).toHaveTextContent("Choose a port from 1 to 65535");
    fireEvent.change(screen.getByLabelText("Remote local port"), { target: { value: "18080" } });
    fetchMock.mockResolvedValueOnce(response("Service is disabled", 409));
    await user.click(screen.getByRole("button", { name: "Download visitor configuration" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Service is disabled");
  });

  it("keeps edits and server errors visible if saving fails", async () => {
    const user = userEvent.setup();
    mount();
    await screen.findByText("Home app");
    await user.click(screen.getByRole("button", { name: "Edit" }));
    await user.clear(screen.getByLabelText("Name"));
    await user.type(screen.getByLabelText("Name"), "Updated app");
    fetchMock.mockResolvedValueOnce(response("Name already exists", 409));
    await user.click(screen.getByRole("button", { name: "Save service" }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Name already exists");
    expect(screen.getByRole("button", { name: "Save service" }).closest("form")).toContainElement(alert);
    expect(alert).toHaveFocus();
    expect(screen.getByLabelText("Name")).toHaveValue("Updated app");
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole("button", { name: "Edit" })).toHaveFocus());
  });

  it.each([
    { locale: "en", add: "Add service", name: "Name", ip: "Home service IPv4 address", port: "Home service port", fallback: "Allow relay fallback", save: "Save service" },
    { locale: "zh", add: "添加服务", name: "名称", ip: "家庭服务 IPv4 地址", port: "家庭服务端口", fallback: "允许中转兜底", save: "保存服务" },
  ])("preserves a failed POST draft and retries from the form in $locale", async (labels) => {
    const user = userEvent.setup();
    mount(labels.locale);
    await screen.findByText("Home app");
    await user.click(screen.getByRole("button", { name: labels.add }));
    await user.type(screen.getByLabelText(labels.name), "Retry app");
    await user.clear(screen.getByLabelText(labels.ip));
    await user.type(screen.getByLabelText(labels.ip), "192.168.1.10");
    await user.clear(screen.getByLabelText(labels.port));
    await user.type(screen.getByLabelText(labels.port), "9090");
    await user.click(screen.getByLabelText(labels.fallback));
    fetchMock.mockResolvedValueOnce(response("Coordinator unavailable", 503));
    await user.click(screen.getByRole("button", { name: labels.save }));
    const alert = await screen.findByRole("alert");
    const save = screen.getByRole("button", { name: labels.save });
    expect(save.closest("form")).toContainElement(alert);
    expect(alert).toHaveTextContent("Coordinator unavailable");
    expect(alert).toHaveFocus();
    expect(save).toBeEnabled();
    expect(screen.getByLabelText(labels.name)).toHaveValue("Retry app");
    expect(screen.getByLabelText(labels.ip)).toHaveValue("192.168.1.10");
    expect(screen.getByLabelText(labels.port)).toHaveValue(9090);
    expect(screen.getByLabelText(labels.fallback)).not.toBeChecked();
    expect(fetchMock).toHaveBeenCalledTimes(2);
    const draft = { name: "Retry app", local_ip: "192.168.1.10", local_port: 9090, enabled: true, fallback_enabled: false };
    const created = { ...snapshot.services[0], ...draft, id: 2 };
    fetchMock.mockResolvedValueOnce(response(created));
    fetchMock.mockResolvedValueOnce(response({ ...snapshot, services: [...snapshot.services, created] }));
    await user.click(save);
    expect(await screen.findByText("Retry app")).toBeInTheDocument();
    expect(screen.queryByLabelText(labels.name)).not.toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    for (const index of [1, 2]) {
      const [url, request] = fetchMock.mock.calls[index];
      expect(url).toMatch(/\/api\/p2p\/services$/);
      expect(request.method).toBe("POST");
      expect(JSON.parse(request.body)).toEqual(draft);
    }
    await waitFor(() => expect(screen.getByRole("button", { name: labels.add })).toHaveFocus());
  });

  it.each(["Add service", "Edit"])("restores the %s opener after cancelling the editor", async (name) => {
    const user = userEvent.setup();
    mount();
    await screen.findByText("Home app");
    await user.click(screen.getByRole("button", { name }));
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    await waitFor(() => expect(screen.getByRole("button", { name })).toHaveFocus());
    expect(screen.queryByRole("button", { name: "Save service" })).not.toBeInTheDocument();
  });

  it.each(["Delete", "Rotate access key"])("restores %s when its confirmation is cancelled", async (name) => {
    const user = userEvent.setup();
    mount();
    await screen.findByText("Home app");
    const trigger = screen.getByRole("button", { name });
    await user.click(trigger);
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    await waitFor(() => expect(trigger).toHaveFocus());
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("closes a persisted edit even if the following refresh fails", async () => {
    const user = userEvent.setup();
    mount();
    await screen.findByText("Home app");
    await user.click(screen.getByRole("button", { name: "Edit" }));
    fetchMock.mockResolvedValueOnce(response(snapshot.services[0]));
    fetchMock.mockResolvedValueOnce(response("Could not refresh status", 502));
    await user.click(screen.getByRole("button", { name: "Save service" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Could not refresh status");
    expect(screen.queryByRole("button", { name: "Save service" })).not.toBeInTheDocument();
  });

  it("exports a custom CA separately without displaying its contents", async () => {
    fetchMock.mockResolvedValueOnce(response({ ...snapshot, provider: { ...snapshot.provider, ca_required: true } }));
    vi.stubGlobal("URL", class extends URL { static createObjectURL = vi.fn(() => "blob:certificate"); static revokeObjectURL = vi.fn(); });
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
    const user = userEvent.setup();
    mount();
    await screen.findByText("Home app");
    expect(screen.getByText(/Save frps-ca.crt beside visitor.toml/)).toBeInTheDocument();
    fetchMock.mockResolvedValueOnce(new Response("certificate-content", { headers: { "Content-Type": "application/x-pem-file" } }));
    await user.click(screen.getByRole("button", { name: "Download server CA certificate" }));
    await waitFor(() => expect(click).toHaveBeenCalledOnce());
    expect(fetchMock.mock.calls[1][0]).toMatch(/\/api\/p2p\/ca$/);
    expect(fetchMock.mock.calls[1][1].headers.get("Authorization")).toBe("Bearer admin-token");
    expect(screen.queryByText("certificate-content")).not.toBeInTheDocument();
  });

  it("requires confirmation before rotating access keys or deleting", async () => {
    const user = userEvent.setup();
    mount();
    await screen.findByText("Home app");
    await user.click(screen.getByRole("button", { name: "Rotate access key" }));
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await user.click(screen.getByRole("button", { name: "Replace key" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    expect(fetchMock.mock.calls[1][0]).toMatch(/\/services\/1\/rotate-key$/);
    await user.click(screen.getByRole("button", { name: "Delete" }));
    expect(fetchMock).toHaveBeenCalledTimes(3);
    await user.click(screen.getByRole("button", { name: "Delete service" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(5));
    expect(fetchMock.mock.calls[3][1].method).toBe("DELETE");
  });

  it("aborts requests and ignores responses after unmount", async () => {
    let finish: (value: Response) => void = () => {};
    fetchMock.mockReturnValueOnce(new Promise<Response>((resolve) => { finish = resolve; }));
    const view = mount();
    const signal = fetchMock.mock.calls[0][1].signal;
    view.unmount();
    expect(signal.aborted).toBe(true);
    await act(async () => finish(response(snapshot)));
  });
});
