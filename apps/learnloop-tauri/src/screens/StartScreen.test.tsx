import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { QueueSnapshot, StartSummaryDto, StreakSummary } from "../api/dto";
import { clear } from "../api/queryCache";
import { STREAK_KEEP_LABEL, StartScreen, minuteChoicesFor } from "./StartScreen";

const { api } = vi.hoisted(() => ({
  api: { getTodayQueue: vi.fn(), startSession: vi.fn(), getStartSummary: vi.fn() }
}));
vi.mock("../api/client", () => ({ api }));

const EMPTY_QUEUE: QueueSnapshot = {
  version: 1,
  generatedAt: "2026-10-11T12:00:00Z",
  sessionId: null,
  sections: [],
  totalItems: 0
};

const NO_STREAK: StreakSummary = { current: 0, activeToday: false, longest: 0 };

function summary(overrides: Partial<StartSummaryDto> = {}): StartSummaryDto {
  const remembered = overrides.rememberedMinutes ?? 25;
  return {
    version: 1,
    rememberedMinutes: remembered,
    minutesSource: "last_session",
    minutesPresets: [10, 15, 25, 40, 60],
    minuteChoices: [...new Set([10, 15, 25, 40, 60, remembered])].sort((a, b) => a - b),
    streak: NO_STREAK,
    ...overrides
  };
}

function showStart({
  startSummary = summary(),
  streak = NO_STREAK
}: { startSummary?: StartSummaryDto | Error; streak?: StreakSummary } = {}) {
  vi.stubGlobal("localStorage", { getItem: vi.fn(() => null), setItem: vi.fn() });
  // jsdom has no layout observer; the decorative backdrop only needs it to exist.
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(null);
  api.getTodayQueue.mockResolvedValue(EMPTY_QUEUE);
  if (startSummary instanceof Error) api.getStartSummary.mockRejectedValue(startSummary);
  else api.getStartSummary.mockResolvedValue(startSummary);
  api.startSession.mockResolvedValue({ sessionId: "s1" });
  const props = { onBegin: vi.fn(), onError: vi.fn(), onNewVault: vi.fn() };
  render(<StartScreen {...props} vault={null} streak={streak} />);
  return props;
}

function chip(minutes: number): HTMLElement {
  return screen.getByRole("radio", { name: `${minutes}m` });
}

async function pressEnter() {
  await act(async () => {
    fireEvent.keyDown(window, { key: "Enter" });
  });
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

// Daily-loop DL0 (spec §6.6, P4): no readiness form, minutes only.
it("asks for minutes only: no energy, sleep or readiness controls", async () => {
  showStart();
  await screen.findByRole("radiogroup", { name: "minutes today" });
  expect(screen.queryByText(/energy/i)).toBeNull();
  expect(screen.queryByText(/sleep/i)).toBeNull();
  expect(screen.queryByText(/readiness/i)).toBeNull();
});

it("defaults to the remembered minutes and begins with exactly those", async () => {
  const props = showStart({ startSummary: summary({ rememberedMinutes: 40 }) });
  await waitFor(() => expect(chip(40).getAttribute("aria-checked")).toBe("true"));
  expect(screen.getByText(/minutes from your last session/)).toBeTruthy();
  // The preview asks for Today's queue with the minutes alone: no energy and no
  // readiness-derived limit (Today never applied one).
  await waitFor(() => expect(api.getTodayQueue).toHaveBeenCalledWith({ availableMinutes: 40 }));
  expect(api.getTodayQueue).toHaveBeenCalledTimes(1);

  await pressEnter();
  expect(api.startSession).toHaveBeenCalledWith({ availableMinutes: 40 });
  await waitFor(() => expect(props.onBegin).toHaveBeenCalledWith({ sessionId: "s1" }));
});

it("offers the one-tap chips 10, 15, 25, 40 and 60, and a tap sets what Begin sends", async () => {
  showStart();
  await waitFor(() => expect(chip(25).getAttribute("aria-checked")).toBe("true"));
  expect(screen.getAllByRole("radio").map((el) => el.textContent)).toEqual(["10m", "15m", "25m", "40m", "60m"]);

  fireEvent.click(chip(15));
  expect(chip(15).getAttribute("aria-checked")).toBe("true");
  await waitFor(() => expect(api.getTodayQueue).toHaveBeenCalledWith({ availableMinutes: 15 }));
  await pressEnter();
  expect(api.startSession).toHaveBeenCalledWith({ availableMinutes: 15 });
});

it("steps through the chips with the arrow keys the key bar names", async () => {
  showStart();
  await waitFor(() => expect(chip(25).getAttribute("aria-checked")).toBe("true"));
  fireEvent.keyDown(window, { key: "ArrowRight" });
  expect(chip(40).getAttribute("aria-checked")).toBe("true");
  fireEvent.keyDown(window, { key: "ArrowLeft" });
  fireEvent.keyDown(window, { key: "ArrowLeft" });
  expect(chip(15).getAttribute("aria-checked")).toBe("true");
});

it("keeps a remembered value that is not a preset visible and selected", async () => {
  showStart({ startSummary: summary({ rememberedMinutes: 30 }) });
  await waitFor(() => expect(chip(30).getAttribute("aria-checked")).toBe("true"));
  expect(screen.getAllByRole("radio").map((el) => el.textContent)).toEqual(["10m", "15m", "25m", "30m", "40m", "60m"]);
  await pressEnter();
  expect(api.startSession).toHaveBeenCalledWith({ availableMinutes: 30 });
});

it("uses 25 minutes on a fresh vault, and when the summary cannot be read", async () => {
  showStart({ startSummary: summary({ rememberedMinutes: 25, minutesSource: "first_run" }) });
  await waitFor(() => expect(chip(25).getAttribute("aria-checked")).toBe("true"));
  expect(screen.getByText(/they are remembered next time/)).toBeTruthy();
  cleanup();
  clear();

  const props = showStart({ startSummary: new Error("unknown method") });
  await waitFor(() => expect(chip(25).getAttribute("aria-checked")).toBe("true"));
  expect(props.onError).toHaveBeenCalled();
  await pressEnter();
  expect(api.startSession).toHaveBeenLastCalledWith({ availableMinutes: 25 });
});

it("computes the chips as the presets plus the minutes in force", () => {
  expect(minuteChoicesFor(null, 25)).toEqual([10, 15, 25, 40, 60]);
  expect(minuteChoicesFor(null, 45)).toEqual([10, 15, 25, 40, 45, 60]);
  expect(minuteChoicesFor(summary({ rememberedMinutes: 30 }), 15)).toEqual([10, 15, 25, 30, 40, 60]);
});

// Daily-loop §8 (D8, gate G11): the streak counts days with a started session,
// so the badge says that instead of "practice today".
it("labels the streak with what it counts", async () => {
  showStart({ startSummary: summary({ streak: { current: 6, activeToday: false, longest: 9 } }) });
  expect(await screen.findByText(new RegExp(STREAK_KEEP_LABEL))).toBeTruthy();
  expect(STREAK_KEEP_LABEL).toBe("begin a session today to keep your streak");
  expect(screen.queryByText(/practice today/i)).toBeNull();
  expect(screen.getByText(/best 9/)).toBeTruthy();
});

it("marks today once a session has begun, reading the fresh streak over the stale snapshot", async () => {
  showStart({
    startSummary: summary({ streak: { current: 7, activeToday: true, longest: 9 } }),
    streak: { current: 6, activeToday: false, longest: 9 }
  });
  expect(await screen.findByText(/today ✓/)).toBeTruthy();
  expect(screen.queryByText(new RegExp(STREAK_KEEP_LABEL))).toBeNull();
});
