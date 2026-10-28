import { cleanup, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ServiceCard } from "@/components/access/service-card";
import { ToastProvider } from "@/components/providers/toast-provider";
import messages from "@/i18n/locales/en.json";
import type { PublishedService } from "@/types/access";

const service: PublishedService = { id: 1, name: "Photos", local_ip: "192.168.1.10", local_port: 8080, public_port: 18080, protocol: "TCP", mode: "auto", domain: "", rr: "@", enabled: true, lease_duration: 3600, status: "healthy", active_mode: "direct", public_endpoint: "203.0.113.1:18080", dns_status: "not_configured", reason_code: "inbound_unverified", last_error: null, last_checked: null, external_verified: false, failure_count: 0 };

function renderService(override: Partial<PublishedService> = {}) {
  return render(<NextIntlClientProvider locale="en" messages={messages} timeZone="UTC">
    <ToastProvider>
      <ServiceCard service={{ ...service, ...override }} busy={false} onEdit={vi.fn()} onDelete={vi.fn()} onCheck={vi.fn()} />
    </ToastProvider>
  </NextIntlClientProvider>);
}

afterEach(cleanup);

describe("public access evidence", () => {
  it("does not equate a healthy local configuration with verified public reachability", () => {
    renderService();
    expect(screen.getByText("Configured · external check pending")).toBeInTheDocument();
    expect(screen.queryByText("Externally verified")).not.toBeInTheDocument();
    expect(screen.getByText(/The route is configured; an external check is still needed/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy the address for Photos" })).toBeInTheDocument();
  });

  it("only presents externally verified status when evidence is present", () => {
    renderService({ external_verified: true, reason_code: "ready" });
    expect(screen.getByText("Externally verified")).toBeInTheDocument();
  });

  it("shows the backend pending-verification result as configured", () => {
    renderService({ status: "pending", reason_code: "relay_unverified", active_mode: "relay" });
    expect(screen.getByText("Configured · external check pending")).toBeInTheDocument();
    expect(screen.queryByText("Externally verified")).not.toBeInTheDocument();
  });

  it("translates actionable relay setup failures", () => {
    renderService({ status: "needs_setup", reason_code: "relay_not_configured", active_mode: null });
    expect(screen.getByRole("status")).toHaveTextContent("An administrator must configure a public relay.");
  });
});
