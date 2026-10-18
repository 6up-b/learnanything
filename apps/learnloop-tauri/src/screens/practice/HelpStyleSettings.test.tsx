// Adaptive hints H2b (spec D5): Settings edits the one stored help style the
// hint panel's "⋯" menu edits, and shows nothing while adaptive hints are off.
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { algoConfig, setAlgoConfig } from "../../app/algoConfig";
import { HelpStyleSettings } from "./HelpStyleSettings";

const { api } = vi.hoisted(() => ({ api: { setHelpStyle: vi.fn() } }));
vi.mock("../../api/client", () => ({ api }));

beforeEach(() => api.setHelpStyle.mockReset());
afterEach(() => {
  cleanup();
  setAlgoConfig(undefined);
});

it("is absent while adaptive hints are off", () => {
  setAlgoConfig({});
  const { container } = render(<HelpStyleSettings rowStyle={{}} labelStyle={{}} onToast={vi.fn()} />);
  expect(container.innerHTML).toBe("");
});

it("writes [hints] help_style through the sidecar and remembers what it saved", async () => {
  setAlgoConfig({ hints: { adaptiveEnabled: true, authoredOfferAfterSeconds: 4, helpStyle: "balanced" } });
  api.setHelpStyle.mockResolvedValue({ version: 1, helpStyle: "let_me_struggle" });
  const onToast = vi.fn();
  render(<HelpStyleSettings rowStyle={{}} labelStyle={{}} onToast={onToast} />);
  const group = screen.getByRole("group", { name: "help style" });
  expect(group.querySelector('[aria-pressed="true"]')?.textContent).toBe("balanced");
  fireEvent.click(screen.getByRole("button", { name: "let me struggle" }));
  await waitFor(() => expect(api.setHelpStyle).toHaveBeenCalledWith("let_me_struggle"));
  await waitFor(() => expect(group.querySelector('[aria-pressed="true"]')?.textContent).toBe("let me struggle"));
  expect(algoConfig().adaptiveHints?.helpStyle).toBe("let_me_struggle");
  expect(onToast).toHaveBeenCalledWith("help style → let me struggle");
});
