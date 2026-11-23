// The desks harness page shows the desks, or, with `?preview=<state>`, one window as a card in that
// lifecycle state (the real-webview check that a preview logs no reading activity reads it).
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

vi.mock("../../screens/desks/DeskShell", () => ({ DeskShell: () => <div data-testid="desks" /> }));
vi.mock("../../screens/desks/windows/SourceWindow", () => ({ SourceWindow: () => <div data-testid="source-window" /> }));

import { Harness } from "./harness";

afterEach(cleanup);

it("shows the desks by default", () => {
  render(<Harness search="" />);
  expect(screen.getByTestId("desks")).toBeTruthy();
});

it("shows one window as a preview card, or as an active one for the control", () => {
  const { container, rerender } = render(<Harness search="?preview=preview" />);
  expect(container.querySelector("[data-preview-card]")).not.toBeNull();
  expect(screen.getByTestId("source-window")).toBeTruthy();
  rerender(<Harness search="?preview=active" />);
  expect(container.querySelector("[data-preview-card]")).not.toBeNull();
  rerender(<Harness search="?preview=other" />);
  expect(screen.getByTestId("desks")).toBeTruthy();
});
