import { lazy, Suspense } from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ScreenErrorBoundary } from "./ScreenErrorBoundary";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

it("shows a reload action when a lazy screen chunk fails to load", async () => {
  vi.spyOn(console, "error").mockImplementation(() => undefined);
  const reload = vi.fn();
  vi.spyOn(window, "location", "get").mockReturnValue({ ...window.location, reload });
  const BrokenScreen = lazy(() => Promise.reject(new Error("Failed to fetch dynamically imported module")));
  render(
    <ScreenErrorBoundary resetKey="reader">
      <Suspense fallback={<div>Loading…</div>}>
        <BrokenScreen />
      </Suspense>
    </ScreenErrorBoundary>
  );
  expect(await screen.findByText("Failed to fetch dynamically imported module")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "reload app" }));
  expect(reload).toHaveBeenCalledOnce();
});

it("clears the error when the active tab changes", async () => {
  vi.spyOn(console, "error").mockImplementation(() => undefined);
  const BrokenScreen = lazy(() => Promise.reject(new Error("chunk missing")));
  const view = render(
    <ScreenErrorBoundary resetKey="reader">
      <Suspense fallback={null}><BrokenScreen /></Suspense>
    </ScreenErrorBoundary>
  );
  await screen.findByText("chunk missing");
  view.rerender(
    <ScreenErrorBoundary resetKey="today">
      <p>Today</p>
    </ScreenErrorBoundary>
  );
  expect(screen.getByText("Today")).toBeTruthy();
});
