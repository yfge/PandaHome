import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { accessRequest } from "@/components/access/access-api";
import { RelaySettings } from "@/components/access/relay-settings";
import english from "@/i18n/locales/en.json";
import chinese from "@/i18n/locales/zh.json";
import { ApiClientError } from "@/lib/api-client";
import type { RelayConfigView, RelayConfigWrite } from "@/types/access";

vi.mock("@/components/access/access-api", () => ({ accessRequest: vi.fn() }));

const config: RelayConfigView = {
  server_addr: "127.0.0.1", server_port: 58354, public_host: "relay.example.test", binary: "frpc",
  tls_trusted_ca_file: "/private/ca.crt", tls_server_name: "relay.internal", ssh_enabled: true,
  ssh_host: "relay.example.test", ssh_port: 22, ssh_user: "operator", ssh_identity_file: "/private/key",
  ssh_known_hosts_file: "/private/known_hosts", ssh_local_port: 0, ssh_binary: "ssh", has_token: true, source: "managed",
};

function show(locale: "en" | "zh") {
  const messages = locale === "en" ? english : chinese;
  render(<NextIntlClientProvider locale={locale} messages={messages}><RelaySettings /></NextIntlClientProvider>);
  return messages.access.relaySettings;
}

function lastWrite() {
  return vi.mocked(accessRequest).mock.calls.filter(([, options]) => options?.method === "PUT").at(-1)?.[1]?.body as RelayConfigWrite;
}

beforeEach(() => { vi.mocked(accessRequest).mockResolvedValue(config); });
afterEach(() => { cleanup(); vi.resetAllMocks(); });

describe.each(["en", "zh"] as const)("managed relay settings (%s)", (locale) => {
  it("saves a complete profile without replacing a token from an empty password field", async () => {
    const user = userEvent.setup();
    const t = show(locale);
    await screen.findByText(t.savedSource);
    expect(screen.getByLabelText(t.token)).toHaveValue("");
    expect(screen.getByText(t.tokenSaved)).toBeInTheDocument();
    expect(screen.getByText(new RegExp(t.sshTitle)).closest("details")).not.toHaveAttribute("open");
    await user.click(screen.getByRole("button", { name: t.save }));
    await screen.findByRole("status");
    const payload = lastWrite();
    expect(payload).not.toHaveProperty("token");
    expect(payload).not.toHaveProperty("has_token");
    expect(payload).not.toHaveProperty("source");
    expect(payload).not.toHaveProperty("clear_token");
    expect(payload).toMatchObject({ server_addr: "127.0.0.1", server_port: 58354, public_host: "relay.example.test", ssh_local_port: 0, ssh_enabled: true, tls_trusted_ca_file: "/private/ca.crt", tls_server_name: "relay.internal" });
  });

  it("replaces a token only when entered and clears the input after confirmation", async () => {
    const user = userEvent.setup();
    const t = show(locale);
    await screen.findByText(t.savedSource);
    await user.type(screen.getByLabelText(t.token), "replacement-test-token");
    await user.click(screen.getByRole("button", { name: t.save }));
    await screen.findByText(t.saved);
    expect(lastWrite().token).toBe("replacement-test-token");
    expect(screen.getByLabelText(t.token)).toHaveValue("");
    expect(screen.queryByText("replacement-test-token")).not.toBeInTheDocument();
  });

  it("requires an explicit action to clear saved credentials", async () => {
    const user = userEvent.setup();
    const t = show(locale);
    await screen.findByText(t.savedSource);
    await user.click(screen.getByLabelText(t.removeToken));
    expect(screen.getByText(t.removeTokenWarning)).toBeInTheDocument();
    expect(screen.getByLabelText(t.token)).toBeDisabled();
    await user.click(screen.getByRole("button", { name: t.save }));
    await screen.findByText(t.saved);
    expect(lastWrite().clear_token).toBe(true);
    expect(lastWrite()).not.toHaveProperty("token");
  });

  it("keeps failed drafts and permits typing and retry without stealing focus", async () => {
    const user = userEvent.setup();
    const t = show(locale);
    await screen.findByText(t.savedSource);
    vi.mocked(accessRequest).mockRejectedValueOnce(new ApiClientError("Connection could not be applied", 503));
    await user.clear(screen.getByLabelText(t.publicHost));
    await user.type(screen.getByLabelText(t.publicHost), "public.example.test");
    await user.type(screen.getByLabelText(t.token), "retry-test-token");
    await user.click(screen.getByRole("button", { name: t.save }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveFocus());
    expect(screen.getByLabelText(t.publicHost)).toHaveValue("public.example.test");
    expect(screen.getByLabelText(t.token)).toHaveValue("retry-test-token");
    const field = screen.getByLabelText(t.publicHost);
    await user.click(field);
    await user.type(field, "x");
    expect(field).toHaveFocus();
    await user.click(screen.getByRole("button", { name: t.save }));
    await screen.findByText(t.saved);
    expect(lastWrite().public_host).toBe("public.example.testx");
    expect(lastWrite().token).toBe("retry-test-token");
    expect(screen.getByLabelText(t.token)).toHaveValue("");
  });

  it("opens SSH validation details and focuses repeated validation errors", async () => {
    const user = userEvent.setup();
    const t = show(locale);
    await screen.findByText(t.savedSource);
    fireEvent.change(screen.getByLabelText(t.publicHost), { target: { value: "" } });
    await user.click(screen.getByRole("button", { name: t.save }));
    expect(screen.getByRole("alert")).toHaveTextContent(t.invalidSsh);
    expect(screen.getByRole("alert")).toHaveFocus();
    expect(screen.getByText(new RegExp(t.sshTitle)).closest("details")).toHaveAttribute("open");
    await user.click(screen.getByRole("button", { name: t.save }));
    expect(screen.getByRole("alert")).toHaveFocus();
    expect(lastWrite()).toBeUndefined();
  });
});

it("shows loading until the profile is available", () => {
  vi.mocked(accessRequest).mockReturnValue(new Promise(() => {}));
  const t = show("en");
  expect(screen.getByRole("status", { name: t.loading })).toBeInTheDocument();
  expect(screen.queryByLabelText(t.token)).not.toBeInTheDocument();
});

it("does not expose a settings form when the administrator API denies access", async () => {
  vi.mocked(accessRequest).mockRejectedValue(new ApiClientError("Forbidden", 403));
  const t = show("zh");
  expect(await screen.findByRole("alert")).toHaveTextContent(t.adminOnly);
  expect(screen.queryByLabelText(t.token)).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: t.retry })).toBeInTheDocument();
});
