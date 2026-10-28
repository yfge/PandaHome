import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { UpnpGatewayManager } from "@/components/upnp/gateway-manager";
import { mappingEndpoint, type UpnpGateway } from "@/components/upnp/gateway-api";

const OUTER = "http://192.168.1.1:5000/rootDesc.xml?device=1&service=wan";
const INNER = "http://192.168.2.1/rootDesc.xml";
const outer: UpnpGateway = {
  device_url: OUTER, host: "192.168.1.1", name: "Public router", external_ip: "8.8.8.8",
  address_scope: "public", is_default: false, reachable: true, error: null,
};
const inner: UpnpGateway = {
  ...outer, device_url: INNER, host: "192.168.2.1", name: "Inner router",
  external_ip: "192.168.1.2", address_scope: "private", is_default: true,
};

vi.mock("@/components/upnp/mapping-list", () => ({
  UpnpMappingList: ({ deviceUrl, onBusyChange }: { deviceUrl?: string; onBusyChange: (busy: boolean) => void }) => (
    <div>
      <output aria-label="Mapping target">{deviceUrl || "default"}</output>
      <input aria-label="Mapping draft" />
      <button onClick={() => onBusyChange(true)}>Start mapping</button>
      <button onClick={() => onBusyChange(false)}>Finish mapping</button>
    </div>
  ),
}));

function response(data: unknown, status = 200) {
  return new Response(JSON.stringify(status === 200 ? { code: 0, data } : { detail: data }), {
    status, headers: { "Content-Type": "application/json" },
  });
}

function mount() {
  return render(
    <NextIntlClientProvider locale="en" messages={{}} timeZone="Asia/Shanghai">
      <UpnpGatewayManager />
    </NextIntlClientProvider>,
  );
}

describe("UPnP gateway selection", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    fetchMock.mockResolvedValue(response({ gateways: [outer, inner], discovery_error: null }));
    vi.stubGlobal("fetch", fetchMock);
  });
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("keeps the existing default until a user selects a target and resets drafts on change", async () => {
    const user = userEvent.setup();
    mount();
    await screen.findByRole("option", { name: /Public router/ });
    expect(screen.getByLabelText("Mapping target")).toHaveTextContent("default");
    await user.type(screen.getByLabelText("Mapping draft"), "do not carry this to another router");
    await user.selectOptions(screen.getByLabelText("Manage mappings on"), OUTER);
    expect(screen.getByLabelText("Mapping target")).toHaveTextContent(OUTER);
    expect(screen.getByLabelText("Mapping draft")).toHaveValue("");
    expect(screen.getByText(/inbound access still needs an external test/)).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText("Manage mappings on"), INNER);
    expect(screen.getByLabelText("Mapping target")).toHaveTextContent(INNER);
    expect(screen.getByText(/another NAT layer remains upstream/)).toBeInTheDocument();
  });

  it("checks a manual device URL and keeps the current selection if inspection fails", async () => {
    const user = userEvent.setup();
    mount();
    await screen.findByRole("option", { name: /Public router/ });
    fetchMock.mockResolvedValueOnce(response(outer));
    await user.type(screen.getByLabelText("Upstream router device description URL"), OUTER);
    await user.click(screen.getByRole("button", { name: "Check and select" }));
    await waitFor(() => expect(screen.getByLabelText("Mapping target")).toHaveTextContent(OUTER));
    const [, request] = fetchMock.mock.calls.at(-1)!;
    expect(JSON.parse(request.body)).toEqual({ device_url: OUTER });
    fetchMock.mockResolvedValueOnce(response("Selected router is unreachable", 502));
    await user.click(screen.getByRole("button", { name: "Check and select" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Selected router is unreachable");
    expect(screen.getByLabelText("Mapping target")).toHaveTextContent(OUTER);
  });

  it("prevents changing routers while a mapping is being edited or saved", async () => {
    const user = userEvent.setup();
    mount();
    await screen.findByRole("option", { name: /Public router/ });
    await user.click(screen.getByRole("button", { name: "Start mapping" }));
    expect(screen.getByLabelText("Manage mappings on")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Discover routers" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Finish mapping" }));
    expect(screen.getByLabelText("Manage mappings on")).toBeEnabled();
  });

  it("ignores discovery responses after unmount", async () => {
    let finish: (value: Response) => void = () => {};
    fetchMock.mockReturnValueOnce(new Promise<Response>((resolve) => { finish = resolve; }));
    const view = mount();
    view.unmount();
    await act(async () => finish(response({ gateways: [outer], discovery_error: null })));
  });

  it("encodes the full description URL on every mapping request", () => {
    const endpoint = new URL(mappingEndpoint(OUTER, 8080, "UDP"));
    expect(endpoint.pathname).toBe("/api/upnp/gateways/mappings/8080");
    expect(endpoint.searchParams.get("device_url")).toBe(OUTER);
    expect(endpoint.searchParams.get("protocol")).toBe("UDP");
    expect(new URL(mappingEndpoint()).pathname).toBe("/api/upnp/mappings");
  });

  it("keeps failed manual checks visible without submitting a mapping", async () => {
    mount();
    await screen.findByRole("option", { name: /Public router/ });
    fetchMock.mockResolvedValueOnce(response("Not a supported IGD", 502));
    fireEvent.change(screen.getByLabelText("Upstream router device description URL"), { target: { value: OUTER } });
    fireEvent.submit(screen.getByRole("button", { name: "Check and select" }).closest("form")!);
    expect(await screen.findByRole("alert")).toHaveTextContent("Not a supported IGD");
    expect(fetchMock.mock.calls.every(([url]) => !String(url).includes("/mappings"))).toBe(true);
  });
});
