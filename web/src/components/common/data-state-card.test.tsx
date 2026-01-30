import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DataStateCard } from "@/components/common/data-state-card";

describe("DataStateCard", () => {
  it("renders title and description", () => {
    render(<DataStateCard title="Oops" description="Something went wrong" />);

    expect(screen.getByText("Oops")).toBeInTheDocument();
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("renders action button", () => {
    const onClick = vi.fn();
    render(<DataStateCard title="Empty" action={{ label: "Retry", onClick }} />);

    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });
});
