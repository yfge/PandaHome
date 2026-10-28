import { cleanup, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";

import { P2pPageClient } from "@/app/p2p/page-client";

const auth = vi.hoisted(() => ({ user: null as { role: string } | null }));
vi.mock("@/components/providers/auth-provider", () => ({ useAuth: () => auth }));
vi.mock("@/components/p2p/p2p-manager", () => ({ P2pManager: () => <p>Administrator service manager</p> }));

function mount() {
  return render(<NextIntlClientProvider locale="en" messages={{}} timeZone="Asia/Shanghai"><P2pPageClient /></NextIntlClientProvider>);
}

afterEach(cleanup);

describe("P2P administrator access", () => {
  it("waits for the current account before mounting the manager", () => {
    auth.user = null;
    mount();
    expect(screen.getByRole("status")).toHaveTextContent("Loading your account");
    expect(screen.queryByText("Administrator service manager")).not.toBeInTheDocument();
  });

  it("explains why ordinary users cannot manage access", () => {
    auth.user = { role: "user" };
    mount();
    expect(screen.getByText(/An administrator account is required/)).toBeInTheDocument();
    expect(screen.queryByText("Administrator service manager")).not.toBeInTheDocument();
  });

  it("mounts the service manager for administrators", () => {
    auth.user = { role: "admin" };
    mount();
    expect(screen.getByText("Administrator service manager")).toBeInTheDocument();
  });
});
