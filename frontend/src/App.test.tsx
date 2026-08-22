import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import App from "./App";

vi.mock("./services/api", () => ({
  getHealth: vi.fn(async () => ({ status: "ok", service: "gnkalgo-api" })),
  getReady: vi.fn(async () => ({
    status: "ok",
    service: "gnkalgo-api",
    checks: { database: "ok", redis: "ok" },
    trading_mode: "PAPER",
  })),
}));

describe("App", () => {
  it("renders the foundation status page", async () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );
    expect(await screen.findByText(/Phase 1 foundation/i)).toBeInTheDocument();
    expect(await screen.findByTestId("health-status")).toHaveTextContent("ok");
  });
});
