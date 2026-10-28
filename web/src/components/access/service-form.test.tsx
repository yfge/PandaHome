import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ServiceForm, validateServiceDraft } from "@/components/access/service-form";
import messages from "@/i18n/locales/en.json";
import type { ServiceDraft } from "@/types/access";

const draft: ServiceDraft = { name: "Photos", local_ip: "192.168.1.10", local_port: 8080, public_port: 18080, protocol: "TCP", mode: "auto", domain: "", rr: "@", enabled: true, lease_duration: 3600 };

afterEach(cleanup);

describe("public service form", () => {
  it.each([
    [{ name: " " }, "requiredName"],
    [{ local_ip: "192.168.1.256" }, "invalidIp"],
    [{ local_ip: "192.168.1" }, "invalidIp"],
    [{ local_ip: "192.168.001.10" }, "invalidIp"],
    [{ public_port: 65536 }, "invalidPort"],
    [{ local_port: 8.5 }, "invalidPort"],
    [{ domain: "https://example.com:8080" }, "invalidDomain"],
    [{ domain: "example.com", rr: "bad host" }, "invalidRr"],
    [{ lease_duration: 30 }, "invalidLease"],
    [{ local_ip: "127.0.0.1", mode: "auto" as const }, "loopbackRequiresRelay"],
  ])("rejects invalid configuration %j", (change, expected) => {
    expect(validateServiceDraft({ ...draft, ...change })).toBe(expected);
  });

  it("allows no domain and defaults to automatic selection", () => {
    expect(validateServiceDraft(draft)).toBeNull();
    render(<NextIntlClientProvider locale="en" messages={messages} timeZone="UTC">
      <ServiceForm service={null} busy={false} error={null} relayAvailable={false} onClose={vi.fn()} onSave={vi.fn()} />
    </NextIntlClientProvider>);
    expect(screen.getByLabelText("Access method")).toHaveValue("auto");
  });

  it("supports explicit relay loopback, permanent leases and international domain names", () => {
    expect(validateServiceDraft({ ...draft, mode: "relay", local_ip: "127.0.0.1", lease_duration: 0, domain: "例子.公司", rr: "@" })).toBeNull();
  });

  it("keeps invalid submissions in the dialog with a helpful error", async () => {
    const onSave = vi.fn();
    render(<NextIntlClientProvider locale="en" messages={messages} timeZone="UTC">
      <ServiceForm service={null} busy={false} error={null} relayAvailable={false} onClose={vi.fn()} onSave={onSave} />
    </NextIntlClientProvider>);
    await userEvent.click(screen.getByRole("button", { name: "Save and maintain" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Enter a name you can recognize.");
    expect(screen.getByRole("alert")).toHaveFocus();
    expect(onSave).not.toHaveBeenCalled();
  });

  it("lets users correct validation without refocusing an earlier save error", async () => {
    const user = userEvent.setup();
    render(<NextIntlClientProvider locale="en" messages={messages} timeZone="UTC">
      <ServiceForm service={null} busy={false} error="Relay unavailable" relayAvailable={false} onClose={vi.fn()} onSave={vi.fn()} />
    </NextIntlClientProvider>);
    await user.click(screen.getByRole("button", { name: "Save and maintain" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Enter a name you can recognize.");
    const name = screen.getByLabelText(messages.access.name);
    await user.type(name, "Family photos");
    expect(name).toHaveValue("Family photos");
    expect(name).toHaveFocus();
    expect(screen.getByRole("alert")).toHaveTextContent("Relay unavailable");
  });
});
