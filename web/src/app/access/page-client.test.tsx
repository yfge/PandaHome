import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import Link from "next/link";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AccessPageClient } from "@/app/access/page-client";
import { accessRequest } from "@/components/access/access-api";
import { useAccessState } from "@/components/access/use-access-state";
import { ToastProvider } from "@/components/providers/toast-provider";
import english from "@/i18n/locales/en.json";
import chinese from "@/i18n/locales/zh.json";
import type { AccessState, PublishedService } from "@/types/access";

vi.mock("@/components/access/access-api", () => ({ accessRequest: vi.fn() }));
vi.mock("@/components/access/use-access-state", () => ({ useAccessState: vi.fn() }));
vi.mock("@/components/access/network-summary", () => ({
  NetworkSummary: () => <button type="button">Network details</button>,
}));

const service: PublishedService = {
  id: 1, name: "Photos", local_ip: "192.168.1.10", local_port: 8080, public_port: 18080,
  protocol: "TCP", mode: "auto", domain: "", rr: "@", enabled: true, lease_duration: 3600,
  status: "pending", active_mode: null, public_endpoint: null, dns_status: "not_configured",
  reason_code: null, last_error: null, last_checked: null, external_verified: false, failure_count: 0,
};
const data: AccessState = {
  network: null,
  relay: { configured: false, available: false, running: false, public_host: null, reason_code: null },
  services: [service], poll_interval_seconds: 30,
};
const reload = vi.fn();

async function tabTo(user: ReturnType<typeof userEvent.setup>, target: HTMLElement) {
  for (let step = 0; step < 25 && document.activeElement !== target; step++) await user.tab();
  expect(target).toHaveFocus();
}

function renderPage(locale: "en" | "zh", empty = false) {
  vi.mocked(useAccessState).mockReturnValue({
    data: { ...data, services: empty ? [] : [service] }, error: null, permissionDenied: false, reload,
  });
  const messages = locale === "en" ? english : chinese;
  render(
    <NextIntlClientProvider locale={locale} messages={messages} timeZone="UTC">
      <ToastProvider><Link href="/">Home</Link><AccessPageClient /></ToastProvider>
    </NextIntlClientProvider>,
  );
  return messages.access;
}

beforeEach(() => { vi.mocked(accessRequest).mockResolvedValue(undefined); });
afterEach(() => { cleanup(); vi.resetAllMocks(); });

describe.each(["en", "zh"] as const)("public dialog keyboard focus (%s)", (locale) => {
  it.each([
    ["header", "escape"], ["header", "cancel"],
    ["empty", "escape"], ["empty", "cancel"],
    ["edit", "escape"], ["edit", "cancel"],
    ["delete", "escape"], ["delete", "cancel"],
  ] as const)("returns from %s dialog via %s without scrolling", async (entry, closeMethod) => {
    const user = userEvent.setup();
    const t = renderPage(locale, entry === "empty");
    const trigger = entry === "edit" || entry === "delete"
      ? screen.getByRole("button", { name: t[entry] })
      : screen.getAllByRole("button", { name: t.addService })[entry === "empty" ? 1 : 0];
    await tabTo(user, trigger);
    await user.keyboard("{Enter}");
    const dialog = await screen.findByRole("dialog");
    expect(dialog).toContainElement(document.activeElement as HTMLElement);
    const focus = vi.spyOn(trigger, "focus");

    if (closeMethod === "escape") await user.keyboard("{Escape}");
    else {
      await tabTo(user, within(dialog).getByRole("button", { name: t.cancel }));
      await user.keyboard("{Enter}");
    }

    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    await waitFor(() => expect(trigger).toHaveFocus());
    expect(focus).toHaveBeenCalledWith({ preventScroll: true });
    if (entry === "header") {
      await user.tab();
      expect(screen.getByRole("button", { name: "Network details" })).toHaveFocus();
    }
    expect(accessRequest).not.toHaveBeenCalled();
  });

  it("returns to the stable add button after deleting its original trigger", async () => {
    const user = userEvent.setup();
    const t = renderPage(locale);
    const add = screen.getByRole("button", { name: t.addService });
    const trigger = screen.getByRole("button", { name: t.delete });
    reload.mockImplementation(async () => {
      vi.mocked(useAccessState).mockReturnValue({
        data: { ...data, services: [] }, error: null, permissionDenied: false, reload,
      });
    });
    await tabTo(user, trigger);
    await user.keyboard("{Enter}");
    const dialog = await screen.findByRole("dialog");
    await tabTo(user, within(dialog).getByRole("button", { name: t.delete }));
    await user.keyboard("{Enter}");

    await waitFor(() => expect(trigger).not.toBeInTheDocument());
    await waitFor(() => expect(add).toHaveFocus());
    expect(accessRequest).toHaveBeenCalledWith("/services/1", expect.objectContaining({ method: "DELETE" }));
  });
});
