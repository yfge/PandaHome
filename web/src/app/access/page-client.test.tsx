import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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
  it.each(["add", "edit", "delete"] as const)("restores %s focus before the next keyboard event", async (entry) => {
    const user = userEvent.setup();
    const t = renderPage(locale);
    const trigger = screen.getByRole("button", { name: entry === "add" ? t.addService : t[entry] });
    await tabTo(user, trigger);
    await user.keyboard("{Enter}");
    const dialog = await screen.findByRole("dialog");

    fireEvent.keyDown(dialog, { key: "Escape", code: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(trigger).toHaveFocus();
    await user.tab({ shift: entry === "delete" });
    const next = screen.getByRole("button", { name: entry === "add" ? "Network details" : entry === "edit" ? t.delete : t.edit });
    expect(next).toHaveFocus();
    await new Promise((resolve) => setTimeout(resolve, 10));
    expect(next).toHaveFocus();
  });

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

  it.each(["add", "edit"] as const)("keeps %s failures in the form, retains the draft and restores focus after retry", async (entry) => {
    const user = userEvent.setup();
    const t = renderPage(locale);
    vi.mocked(accessRequest).mockRejectedValueOnce(new Error("Relay unavailable"));
    const trigger = screen.getByRole("button", { name: entry === "add" ? t.addService : t.edit });
    await tabTo(user, trigger);
    await user.keyboard("{Enter}");
    const dialog = await screen.findByRole("dialog");
    const name = within(dialog).getByLabelText(t.name);
    await user.clear(name);
    await user.type(name, "Family photos");
    if (entry === "add") await user.type(within(dialog).getByLabelText(t.localIp), "192.168.1.10");
    const save = within(dialog).getByRole("button", { name: t.save });
    await tabTo(user, save);
    await user.keyboard("{Enter}");

    const alert = await within(dialog).findByRole("alert");
    expect(alert).toHaveTextContent("Relay unavailable");
    await waitFor(() => expect(alert).toHaveFocus());
    expect(dialog.querySelector("form")).toContainElement(document.activeElement as HTMLElement);
    expect(name).toHaveValue("Family photos");
    expect(within(dialog).getByLabelText(t.localIp)).toHaveValue("192.168.1.10");
    expect(save).toBeEnabled();

    await tabTo(user, save);
    await user.keyboard("{Enter}");
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    await waitFor(() => expect(trigger).toHaveFocus());
    expect(accessRequest).toHaveBeenCalledTimes(2);
    expect(accessRequest).toHaveBeenLastCalledWith(entry === "add" ? "/services" : "/services/1", expect.objectContaining({
      method: entry === "add" ? "POST" : "PUT",
      body: expect.objectContaining({ name: "Family photos", local_ip: "192.168.1.10" }),
    }));
  });
});
