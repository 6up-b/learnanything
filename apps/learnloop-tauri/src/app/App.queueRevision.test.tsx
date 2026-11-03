// Mobile PR-7 (spec_mobile_tailnet_v1 §3.3): the revision poll runs at app level, in the App.
// With an answer open, a phone's change re-reads the session (session_moved) and holds the
// plan's refetch until the learner leaves the question; the answer's screen is not remounted.
// On Today, an idle tick costs the token alone.
import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { clear } from "../api/queryCache";

const stubs = vi.hoisted(() => ({
  config: {} as Record<string, unknown>,
  session: null as Record<string, unknown> | null,
  api: {} as Record<string, (...args: unknown[]) => unknown>,
  practiceMounts: 0,
  practiceProps: null as Record<string, unknown> | null
}));

vi.mock("@tauri-apps/api/event", () => ({ listen: vi.fn(async () => () => undefined) }));
vi.mock("@tauri-apps/plugin-dialog", () => ({ open: vi.fn(async () => null) }));
vi.mock("../components/useSourceFileDrop", () => ({ useSourceFileDrop: () => false, pickSourceFiles: async () => [] }));
vi.mock("../components/InboxStrip", () => ({ InboxStrip: () => null }));

vi.mock("../api/client", () => {
  const base: Record<string, unknown> = {
    loadVault: vi.fn(async () => ({
      vault: { root: "/vault", subjects: [], subjectTitles: [], counts: { learningObjects: 4, practiceItems: 6 }, algorithmVersion: "mvp-0.43" },
      health: { ai: { ready: true, settingsReady: true, manualGrading: false, activeProvider: "chatgpt_plan" }, codex: { ready: false } },
      config: stubs.config,
      activeSession: stubs.session,
      streak: { current: 4, activeToday: false, longest: 9 }
    })),
    getSourceLibrary: vi.fn(async () => ({ sources: [], pending: [] }))
  };
  const api = new Proxy(base, {
    get: (target, name: string) => {
      if (name in stubs.api) return stubs.api[name];
      return name in target ? target[name] : () => new Promise(() => undefined);
    }
  });
  return { api };
});

function stub(name: string) {
  return () => <div data-testid={name}>{name}</div>;
}

vi.mock("../screens/ReaderScreen", () => ({ ReaderScreen: stub("reader-stub") }));
vi.mock("../screens/LibraryPlace", () => ({ LibraryPlace: stub("library-stub") }));
vi.mock("../screens/StartScreen", () => ({ StartScreen: stub("start-stub") }));
vi.mock("../screens/TodayScreen", () => ({ TodayScreen: stub("today-stub") }));
vi.mock("../screens/PracticeScreen", async () => {
  const { useEffect } = await import("react");
  return {
    PracticeScreen: (props: Record<string, unknown>) => {
      stubs.practiceProps = props;
      useEffect(() => {
        stubs.practiceMounts += 1;
      }, []);
      return <div data-testid="practice-stub">practice</div>;
    }
  };
});
vi.mock("../screens/GraphScreen", () => ({ GraphScreen: stub("graph-stub") }));
vi.mock("../screens/IngestScreen", () => ({ IngestScreen: stub("ingest-stub") }));
vi.mock("../screens/ProposalsScreen", () => ({ ProposalsScreen: stub("proposals-stub") }));
vi.mock("../screens/RegistryReviewScreen", () => ({ RegistryReviewScreen: stub("registry-stub") }));
vi.mock("../screens/MaintenanceScreen", () => ({ MaintenanceScreen: stub("maintain-stub") }));
vi.mock("../screens/ReviewScreen", () => ({ ReviewScreen: stub("review-stub") }));
vi.mock("../screens/SettingsScreen", () => ({ SettingsOverlay: stub("settings-stub") }));
vi.mock("../screens/reader/WrapUpOffer", () => ({ WrapUpOffer: () => null }));

import { App } from "./App";
import { REVISION_POLL_MS } from "./useQueueRevisionPoll";

const SESSION = {
  version: 1, sessionId: "ses_1", startedAt: "2026-11-03T00:00:00Z", endedAt: null, energy: null, sleepQuality: null,
  availableMinutes: 25, notesMdPath: null,
  checkpoint: {
    sessionId: "ses_1", currentPracticeItemId: "pi_1", currentAnswer: "half an answer", hintsUsed: 0, submissionId: "sub_1",
    focusBlockState: null, pendingGradingProposal: null, readiness: null, updatedAt: "2026-11-03T00:00:00Z"
  }
};

async function wait(ms: number) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

beforeEach(() => {
  clear();
  const store = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => { store.set(key, value); },
    removeItem: (key: string) => { store.delete(key); },
    clear: () => store.clear()
  });
  Element.prototype.scrollIntoView = () => undefined;
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  vi.stubGlobal("IntersectionObserver", class { observe() {} unobserve() {} disconnect() {} takeRecords() { return []; } });
  vi.useFakeTimers();
  stubs.config = { shell: "simple" };
  stubs.session = null;
  stubs.practiceMounts = 0;
  stubs.practiceProps = null;
  stubs.api = {
    getQueueRevision: vi.fn(async () => ({ version: 1, revision: 1, updatedAt: null })),
    getSession: vi.fn(async () => SESSION),
    getDailyPlan: vi.fn(async () => ({ version: 1, enabled: false, plan: null, reason: "plan_disabled" })),
    getReviewCounts: vi.fn(async () => ({ proposalsBadge: 0, maintainBadge: 0 }))
  };
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("the app-level revision poll", () => {
  it("runs on the question screen, holds the plan's refetch and keeps the answer's screen mounted", async () => {
    stubs.session = SESSION;
    render(<App />);
    await wait(0);
    await wait(0);
    expect(screen.getByTestId("practice-stub")).toBeTruthy();
    const planReads = vi.mocked(stubs.api.getDailyPlan).mock.calls.length;
    await wait(REVISION_POLL_MS * 3);
    expect(vi.mocked(stubs.api.getQueueRevision).mock.calls.length).toBeGreaterThanOrEqual(3);
    expect(stubs.api.getSession).not.toHaveBeenCalled();

    // The phone adopted the session: the token moves.
    stubs.api.getQueueRevision = vi.fn(async () => ({ version: 1, revision: 2, updatedAt: null }));
    stubs.api.getSession = vi.fn(async () => ({ ...SESSION, ownerDeviceId: "dev_phone", ownerLabel: "Phone", ownerGeneration: 1 }));
    await wait(REVISION_POLL_MS * 2);

    expect(stubs.api.getSession).toHaveBeenCalledTimes(1);
    expect(stubs.api.getDailyPlan).toHaveBeenCalledTimes(planReads);
    expect(stubs.practiceMounts).toBe(1);
    expect(screen.getByTestId("practice-stub")).toBeTruthy();
  });

  it("refetches the plan once when the learner leaves the question", async () => {
    stubs.session = SESSION;
    render(<App />);
    await wait(0);
    await wait(0);
    stubs.api.getQueueRevision = vi.fn(async () => ({ version: 1, revision: 2, updatedAt: null }));
    await wait(REVISION_POLL_MS * 2);
    const held = vi.mocked(stubs.api.getDailyPlan).mock.calls.length;

    await act(async () => {
      (stubs.practiceProps?.onBack as () => void)();
      await vi.advanceTimersByTimeAsync(0);
    });
    await wait(0);
    expect(vi.mocked(stubs.api.getDailyPlan).mock.calls.length).toBeGreaterThan(held);
    const afterLeaving = vi.mocked(stubs.api.getDailyPlan).mock.calls.length;

    await wait(REVISION_POLL_MS * 3);
    expect(stubs.api.getDailyPlan).toHaveBeenCalledTimes(afterLeaving);
  });

  it("an idle Today reads the token and refetches nothing", async () => {
    render(<App />);
    await wait(0);
    await wait(0);
    const reads = Object.fromEntries(
      Object.entries(stubs.api).map(([name, fn]) => [name, vi.mocked(fn).mock.calls.length])
    );
    await wait(REVISION_POLL_MS * 5);

    expect(vi.mocked(stubs.api.getQueueRevision).mock.calls.length).toBe(reads.getQueueRevision + 5);
    expect(stubs.api.getDailyPlan).toHaveBeenCalledTimes(reads.getDailyPlan);
    expect(stubs.api.getReviewCounts).toHaveBeenCalledTimes(reads.getReviewCounts);
  });
});
