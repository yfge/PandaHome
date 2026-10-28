import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/providers/toast-provider";
import { UpnpMappingList } from "@/components/upnp/mapping-list";
import messages from "@/i18n/locales/en.json";

const mapping = {
  description: "NAS", internal_ip: "192.168.1.10", internal_port: 80,
  external_port: 8080, protocol: "TCP", enabled: true, lease_duration: 0,
};

function mount(mappings = [mapping]) {
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({
    code: 0, data: { mappings },
  }), { headers: { "Content-Type": "application/json" } })));
  return render(
    <NextIntlClientProvider locale="en" messages={messages} timeZone="Asia/Shanghai">
      <ToastProvider>
        <a href="#home">Home</a>
        <UpnpMappingList />
      </ToastProvider>
    </NextIntlClientProvider>,
  );
}

describe("UPnP mapping dialogs", () => {
  beforeEach(() => {
    vi.stubGlobal("ResizeObserver", class {
      observe() {}
      unobserve() {}
      disconnect() {}
    });
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it.each(["Escape", "Cancel", "Close"])("returns to Add Mapping after %s and continues Tab to the row actions", async (dismiss) => {
    const user = userEvent.setup();
    mount();
    const actions = await screen.findByRole("button", { name: "Actions for NAS" });
    const trigger = screen.getByRole("button", { name: "Add Mapping" });
    trigger.focus();
    await user.keyboard("{Enter}");
    await screen.findByRole("dialog", { name: "Add Mapping" });
    const focus = vi.spyOn(trigger, "focus");
    if (dismiss === "Escape") await user.keyboard("{Escape}");
    else await user.click(screen.getByRole("button", { name: dismiss }));
    await waitFor(() => expect(trigger).toHaveFocus());
    expect(focus).toHaveBeenCalledWith({ preventScroll: true });
    await user.tab();
    expect(actions).toHaveFocus();
    expect(screen.getByRole("link", { name: "Home" })).not.toHaveFocus();
  });

  it.each([
    ["Add", "Escape"], ["Add", "Cancel"],
    ["Edit", "Escape"], ["Edit", "Cancel"],
    ["Delete", "Escape"], ["Delete", "Cancel"],
  ])("restores %s during %s closure before another key, without a late focus reset", async (action, dismiss) => {
    const readStyle = window.getComputedStyle.bind(window);
    vi.spyOn(window, "getComputedStyle").mockImplementation((element, pseudo) => {
      const style = readStyle(element, pseudo);
      if (!["dialog-content", "dialog-overlay"].includes(element.getAttribute("data-slot") ?? "")) return style;
      // Model the real CSS exit animation, which jsdom does not otherwise run.
      return new Proxy(style, { get: (target, key) => key === "animationName"
        ? element.getAttribute("data-state") === "closed" ? "dialog-exit" : "dialog-enter"
        : Reflect.get(target, key) });
    });
    const user = userEvent.setup();
    mount();
    const actions = await screen.findByRole("button", { name: "Actions for NAS" });
    let trigger: HTMLElement = screen.getByRole("button", { name: "Add Mapping" });
    if (action !== "Add") {
      actions.focus();
      await user.keyboard("{Enter}");
      trigger = await screen.findByRole("menuitem", { name: action });
    }
    trigger.focus();
    await user.keyboard("{Enter}");
    const dialog = await screen.findByRole("dialog");
    if (dismiss === "Escape") fireEvent.keyDown(dialog, { key: "Escape", code: "Escape" });
    else fireEvent.click(within(dialog).getByRole("button", { name: "Cancel" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(trigger).toHaveFocus();
    await user.tab();
    const next = action === "Add" ? actions : screen.getByRole("menuitem", { name: action === "Edit" ? "Delete" : "Edit" });
    if (action !== "Add") await user.keyboard(action === "Edit" ? "{ArrowDown}" : "{ArrowUp}");
    expect(next).toHaveFocus();
    await new Promise((resolve) => setTimeout(resolve, 250));
    expect(next).toHaveFocus();
    expect(screen.getByRole("link", { name: "Home", hidden: true })).not.toHaveFocus();
  });

  it("returns to the empty-list Add entry when that entry opened the dialog", async () => {
    const user = userEvent.setup();
    mount([]);
    const trigger = await screen.findByRole("button", { name: "Add" });
    await user.click(trigger);
    await screen.findByRole("dialog", { name: "Add Mapping" });
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    await waitFor(() => expect(trigger).toHaveFocus());
  });

  it.each([
    ["Edit", "Cancel"], ["Edit", "Escape"], ["Delete", "Cancel"], ["Delete", "Escape"],
  ])("returns to the %s menu item after %s", async (action, dismiss) => {
    const user = userEvent.setup();
    mount();
    const trigger = await screen.findByRole("button", { name: "Actions for NAS" });
    trigger.focus();
    await user.keyboard("{Enter}");
    const item = await screen.findByRole("menuitem", { name: action });
    item.focus();
    await user.keyboard("{Enter}");
    await screen.findByRole("dialog", { name: action === "Edit" ? "Edit Mapping" : "Confirm Delete" });
    const focus = vi.spyOn(item, "focus");
    if (dismiss === "Escape") await user.keyboard("{Escape}");
    else await user.click(screen.getByRole("button", { name: "Cancel" }));
    await waitFor(() => expect(item).toHaveFocus());
    expect(focus).toHaveBeenCalledWith({ preventScroll: true });
  });

  it("waits for an in-flight write before restoring its temporarily disabled Add button", async () => {
    const user = userEvent.setup();
    mount();
    await screen.findByRole("button", { name: "Actions for NAS" });
    const trigger = screen.getByRole("button", { name: "Add Mapping" });
    let finish: (response: Response) => void = () => {};
    vi.mocked(fetch).mockImplementationOnce(() => new Promise<Response>((resolve) => { finish = resolve; }));
    await user.click(trigger);
    await screen.findByRole("dialog", { name: "Add Mapping" });
    await user.type(screen.getByLabelText("Internal IP"), "192.168.1.11");
    await user.type(screen.getByLabelText("Internal port"), "80");
    await user.type(screen.getByLabelText("External port"), "9090");
    await user.click(screen.getByRole("button", { name: "Add" }));
    expect(trigger).toBeDisabled();
    await user.keyboard("{Escape}");
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    finish(new Response(JSON.stringify({ code: 0, data: { status: "success" } }), {
      headers: { "Content-Type": "application/json" },
    }));
    await waitFor(() => expect(trigger).toHaveFocus());
  });

  it("does not steal later navigation when a disabled opener becomes available", async () => {
    const user = userEvent.setup();
    mount();
    await screen.findByRole("button", { name: "Actions for NAS" });
    let finish: (response: Response) => void = () => {};
    vi.mocked(fetch).mockImplementationOnce(() => new Promise<Response>((resolve) => { finish = resolve; }));
    await user.click(screen.getByRole("button", { name: "Add Mapping" }));
    await user.type(screen.getByLabelText("Internal IP"), "192.168.1.11");
    await user.type(screen.getByLabelText("Internal port"), "80");
    await user.type(screen.getByLabelText("External port"), "9090");
    await user.click(screen.getByRole("button", { name: "Add" }));
    await user.keyboard("{Escape}");
    const home = screen.getByRole("link", { name: "Home" });
    home.focus();
    finish(new Response(JSON.stringify({ code: 0, data: { status: "success" } }), {
      headers: { "Content-Type": "application/json" },
    }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Add Mapping" })).toBeEnabled());
    expect(home).toHaveFocus();
  });

  it.each(["Edit", "Delete"])("defers a disabled %s menu opener and restores it after a failed write", async (action) => {
    const user = userEvent.setup();
    mount();
    await user.click(await screen.findByRole("button", { name: "Actions for NAS" }));
    const item = await screen.findByRole("menuitem", { name: action });
    await user.click(item);
    const dialog = await screen.findByRole("dialog");
    let finish: (response: Response) => void = () => {};
    vi.mocked(fetch).mockImplementationOnce(() => new Promise<Response>((resolve) => { finish = resolve; }));
    await user.click(within(dialog).getByRole("button", { name: action === "Edit" ? "Save" : "Delete" }));
    expect(item).toHaveAttribute("aria-disabled", "true");
    const focus = vi.spyOn(item, "focus");
    fireEvent.keyDown(dialog, { key: "Escape", code: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(focus).not.toHaveBeenCalled();
    finish(new Response(JSON.stringify({ detail: "Gateway unavailable" }), {
      status: 503, headers: { "Content-Type": "application/json" },
    }));
    await waitFor(() => expect(item).toHaveFocus());
    expect(focus).toHaveBeenCalledWith({ preventScroll: true });
  });

  it("shows an add failure inside the dialog, keeps the full draft and retries the same request", async () => {
    const user = userEvent.setup();
    mount();
    await screen.findByRole("button", { name: "Actions for NAS" });
    const trigger = screen.getByRole("button", { name: "Add Mapping" });
    await user.click(trigger);
    const dialog = await screen.findByRole("dialog", { name: "Add Mapping" });
    await user.click(within(dialog).getByRole("button", { name: "Add" }));
    expect(within(dialog).getByLabelText("Internal IP")).toHaveAttribute("aria-invalid", "true");
    expect(within(dialog).getByText(messages.upnp.form.required)).toBeInTheDocument();
    expect(within(dialog).getAllByText(messages.upnp.form.invalidPort)).toHaveLength(2);
    await user.type(within(dialog).getByLabelText("Description"), "Backup service");
    await user.selectOptions(within(dialog).getByLabelText("Protocol"), "UDP");
    await user.type(within(dialog).getByLabelText("Internal IP"), "192.168.1.42");
    await user.type(within(dialog).getByLabelText("Internal port"), "8081");
    await user.type(within(dialog).getByLabelText("External port"), "18081");
    vi.mocked(fetch).mockResolvedValueOnce(new Response(JSON.stringify({ detail: "UPnP gateway unavailable" }), {
      status: 503, headers: { "Content-Type": "application/json" },
    }));
    await user.click(within(dialog).getByRole("button", { name: "Add" }));
    const alert = await within(dialog).findByRole("alert");
    expect(alert).toHaveTextContent("UPnP gateway unavailable");
    expect(alert).toHaveFocus();
    expect(within(dialog).getByLabelText("Description")).toHaveValue("Backup service");
    expect(within(dialog).getByLabelText("Protocol")).toHaveValue("UDP");
    expect(within(dialog).getByLabelText("Internal IP")).toHaveValue("192.168.1.42");
    expect(within(dialog).getByLabelText("Internal port")).toHaveValue(8081);
    expect(within(dialog).getByLabelText("External port")).toHaveValue(18081);
    expect(within(dialog).getByLabelText("Internal IP")).toHaveAttribute("aria-invalid", "false");
    expect(dialog.querySelectorAll('[aria-invalid="true"]')).toHaveLength(0);
    expect(within(dialog).queryByText(messages.upnp.form.required)).not.toBeInTheDocument();
    expect(within(dialog).queryByText(messages.upnp.form.invalidPort)).not.toBeInTheDocument();
    expect(within(dialog).getByRole("button", { name: "Add" })).toBeEnabled();
    await user.click(within(dialog).getByRole("button", { name: "Add" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    const writes = vi.mocked(fetch).mock.calls.filter(([, init]) => init?.method === "POST");
    expect(writes).toHaveLength(2);
    expect(writes[1][1]?.body).toEqual(writes[0][1]?.body);
    await waitFor(() => expect(trigger).toHaveFocus());
  });

  it("keeps an edited draft across parent rerenders and permits retry after a gateway failure", async () => {
    const user = userEvent.setup();
    mount();
    const actions = await screen.findByRole("button", { name: "Actions for NAS" });
    actions.focus();
    await user.keyboard("{Enter}");
    const item = await screen.findByRole("menuitem", { name: "Edit" });
    item.focus();
    await user.keyboard("{Enter}");
    const dialog = await screen.findByRole("dialog", { name: "Edit Mapping" });
    await user.clear(within(dialog).getByLabelText("Description"));
    await user.type(within(dialog).getByLabelText("Description"), "Revised NAS");
    await user.clear(within(dialog).getByLabelText("Internal port"));
    await user.type(within(dialog).getByLabelText("Internal port"), "8081");
    vi.mocked(fetch).mockResolvedValueOnce(new Response(JSON.stringify({ detail: "Gateway rejected the edit" }), {
      status: 503, headers: { "Content-Type": "application/json" },
    }));
    await user.click(within(dialog).getByRole("button", { name: "Save" }));
    expect(await within(dialog).findByRole("alert")).toHaveTextContent("Gateway rejected the edit");
    expect(within(dialog).getByLabelText("Description")).toHaveValue("Revised NAS");
    expect(within(dialog).getByLabelText("Internal port")).toHaveValue(8081);
    await user.click(within(dialog).getByRole("button", { name: "Save" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    const write = vi.mocked(fetch).mock.calls.find(([, init]) => init?.method === "POST");
    expect(JSON.parse(String(write?.[1]?.body))).toMatchObject({ description: "Revised NAS", internal_port: 8081 });
  });

  it("shows delete failures in the confirmation, keeps its opener and allows a later retry", async () => {
    const user = userEvent.setup();
    mount();
    const actions = await screen.findByRole("button", { name: "Actions for NAS" });
    actions.focus();
    await user.keyboard("{Enter}");
    const item = await screen.findByRole("menuitem", { name: "Delete" });
    item.focus();
    await user.keyboard("{Enter}");
    let dialog = await screen.findByRole("dialog", { name: "Confirm Delete" });
    vi.mocked(fetch).mockResolvedValueOnce(new Response(JSON.stringify({ detail: "Gateway rejected deletion" }), {
      status: 503, headers: { "Content-Type": "application/json" },
    }));
    await user.click(within(dialog).getByRole("button", { name: "Delete" }));
    const alert = await within(dialog).findByRole("alert");
    expect(alert).toHaveTextContent("Gateway rejected deletion");
    expect(alert).toHaveFocus();
    expect(within(dialog).getByRole("button", { name: "Delete" })).toBeEnabled();
    await user.click(within(dialog).getByRole("button", { name: "Cancel" }));
    await waitFor(() => expect(item).toHaveFocus());
    await user.keyboard("{Enter}");
    dialog = await screen.findByRole("dialog", { name: "Confirm Delete" });
    expect(within(dialog).queryByRole("alert")).not.toBeInTheDocument();
    vi.mocked(fetch)
      .mockResolvedValueOnce(new Response(JSON.stringify({ code: 0, data: { status: "success" } }), {
        headers: { "Content-Type": "application/json" },
      }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ code: 0, data: { mappings: [] } }), {
        headers: { "Content-Type": "application/json" },
      }));
    await user.click(within(dialog).getByRole("button", { name: "Delete" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(vi.mocked(fetch).mock.calls.filter(([, init]) => init?.method === "DELETE")).toHaveLength(2);
    await waitFor(() => expect(screen.getByRole("button", { name: "Add Mapping" })).toHaveFocus());
  });
});
