import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { QueueSnapshot } from "../api/dto";
import { clear } from "../api/queryCache";
import { StartScreen } from "./StartScreen";

const { api } = vi.hoisted(() => ({ api: { getTodayQueue: vi.fn(), startSession: vi.fn() } }));
vi.mock("../api/client", () => ({ api }));

const EMPTY_QUEUE: QueueSnapshot = {
  version: 1,
  generatedAt: "2026-10-11T12:00:00Z",
  sessionId: null,
  sections: [],
  totalItems: 0
};

function showStart() {
  vi.stubGlobal("localStorage", { getItem: vi.fn(() => null), setItem: vi.fn() });
  // jsdom has no layout observer; the decorative backdrop only needs it to exist.
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(null);
  api.getTodayQueue.mockResolvedValue(EMPTY_QUEUE);
  return render(
    <StartScreen
      onBegin={vi.fn()}
      onError={vi.fn()}
      vault={null}
      streak={{ current: 0, activeToday: false, longest: 0 }}
      onNewVault={vi.fn()}
    />
  );
}

afterEach(() => { cleanup(); clear(); vi.unstubAllGlobals(); vi.restoreAllMocks(); });

// Daily-loop audit (2026-10-11): the Start screen showed a "postpone" control with
// no handler. Nothing in the app can postpone a session (no reminder, no deferred
// start, no sidecar method), so the control must not be offered at all.
it("offers no dead postpone control next to begin session", async () => {
  showStart();
  expect((await screen.findAllByText(/begin session/)).length).toBeGreaterThan(0);
  expect(screen.queryByText(/postpone/i)).toBeNull();
});
