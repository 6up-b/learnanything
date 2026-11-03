// Mobile PR-7 (spec_mobile_tailnet_v1 §3.3): the revision poll runs at app level, in the App.
// With an answer open, a phone's change re-reads the session (session_moved) and holds the
// plan's refetch until the learner leaves the question; the answer's screen is not remounted.
// On Today, an idle tick costs the token alone. Ruling R2: refetches and reloads run only on
// Today's list; everywhere else a change waits for the return to it and the session is still read.
import { act, cleanup, fireEvent, render, renderHook, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { clear } from "../api/queryCache";

const stubs = vi.hoisted(() => ({
  config: {} as Record<string, unknown>,
  session: null as Record<string, unknown> | null,
  api: {} as Record<string, (...args: unknown[]) => unknown>,
  practiceMounts: 0,
  practiceProps: null as Record<string, unknown> | null,
  todayProps: null as Record<string, unknown> | null,
  lessonProps: null as Record<string, unknown> | null,
  examProps: null as Record<string, unknown> | null
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
vi.mock("../screens/today/TodayPlace", () => ({
  TodayPlace: (props: Record<string, unknown>) => {
    stubs.todayProps = props;
    return <div data-testid="today-place-stub">today</div>;
  }
}));
vi.mock("../screens/LessonScreen", () => ({
  LessonScreen: (props: Record<string, unknown>) => {
    stubs.lessonProps = props;
    return <div data-testid="lesson-stub">lesson</div>;
  }
}));
vi.mock("../screens/ExamScreen", () => ({
  ExamScreen: (props: Record<string, unknown>) => {
    stubs.examProps = props;
    return <div data-testid="exam-stub">exam</div>;
  }
}));
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
import { REVISION_POLL_MS, useSessionMoved } from "./useQueueRevisionPoll";

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

describe("M2a (§6.5): the session moved to the phone", () => {
  const MOVED = { ...SESSION, ownerDeviceId: "dev_phone", ownerLabel: "Phone", ownerGeneration: 1 };

  async function openOnPractice(session: Record<string, unknown> = SESSION) {
    stubs.session = session;
    render(<App />);
    await wait(0);
    await wait(0);
  }

  async function phoneTakesIt() {
    stubs.api.getQueueRevision = vi.fn(async () => ({ version: 1, revision: 2, updatedAt: null }));
    stubs.api.getSession = vi.fn(async () => MOVED);
    await wait(REVISION_POLL_MS * 2);
  }

  it("the banner names the phone, and the question stops writing without being remounted", async () => {
    await openOnPractice();
    expect(stubs.practiceProps?.sessionMoved).toBe(false);
    await phoneTakesIt();
    expect(screen.getByRole("status", { name: "Session moved" }).textContent).toContain("This session continued on Phone.");
    expect(stubs.practiceProps?.sessionMoved).toBe(true);
    expect(stubs.practiceMounts).toBe(1);
  });

  it("a session the phone already holds at load is a move at once, with no read of its own", async () => {
    await openOnPractice(MOVED);
    expect(screen.getByRole("status", { name: "Session moved" })).toBeTruthy();
    expect(stubs.api.getSession).not.toHaveBeenCalled();
  });

  it("a write refused with session_moved says so before the poll's next read", async () => {
    const { noteSessionMovedError } = await import("./sessionMoved");
    await openOnPractice();
    expect(screen.queryByRole("status", { name: "Session moved" })).toBeNull();
    await act(async () => {
      noteSessionMovedError({ code: "session_moved", message: "m", details: { session_id: "ses_1", owner_label: "Phone", owner_generation: 4 } });
    });
    expect(screen.getByRole("status", { name: "Session moved" }).textContent).toContain("Phone");
  });

  it("Take it back adopts at the generation it saw and reopens the question on the checkpoint", async () => {
    await openOnPractice();
    await phoneTakesIt();
    const back = { ...SESSION, ownerGeneration: 2, checkpoint: { ...SESSION.checkpoint, currentAnswer: "the phone's answer" } };
    stubs.api.adoptSession = vi.fn(async () => ({}));
    stubs.api.getSession = vi.fn(async () => back);
    fireEvent.click(screen.getByRole("button", { name: "Take it back" }));
    await wait(0);
    await wait(0);
    expect(stubs.api.adoptSession).toHaveBeenCalledWith({ sessionId: "ses_1", expectedGeneration: 1 });
    expect(screen.queryByRole("status", { name: "Session moved" })).toBeNull();
    expect(stubs.practiceProps?.sessionMoved).toBe(false);
    expect(stubs.practiceMounts).toBe(2);
    expect((stubs.practiceProps?.session as { checkpoint: { currentAnswer: string } }).checkpoint.currentAnswer).toBe("the phone's answer");
  });

  it("Start fresh names the session it replaces", async () => {
    await openOnPractice();
    await phoneTakesIt();
    stubs.api.startSession = vi.fn(async () => ({ ...SESSION, sessionId: "ses_2", checkpoint: null }));
    fireEvent.click(screen.getByRole("button", { name: "Start fresh" }));
    await wait(0);
    await wait(0);
    expect(stubs.api.startSession).toHaveBeenCalledWith({ availableMinutes: 25, replace: "ses_1" });
    expect(screen.queryByRole("status", { name: "Session moved" })).toBeNull();
  });

  it("a session ended elsewhere offers no taking back", async () => {
    await openOnPractice();
    stubs.api.getQueueRevision = vi.fn(async () => ({ version: 1, revision: 2, updatedAt: null }));
    stubs.api.getSession = vi.fn(async () => ({ ...SESSION, endedAt: "2026-11-03T01:00:00Z" }));
    await wait(REVISION_POLL_MS * 2);
    expect(screen.getByRole("status", { name: "Session moved" }).textContent).toContain("ended on another device");
    expect(screen.queryByRole("button", { name: "Take it back" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "OK" }));
    await wait(0);
    expect(screen.queryByRole("status", { name: "Session moved" })).toBeNull();
    expect(screen.queryByTestId("practice-stub")).toBeNull();
  });

  it("open item 6: a phone's change on Today refetches once, and a focus at the same token nothing", async () => {
    stubs.session = { ...SESSION, checkpoint: null };
    stubs.config = { shell: "simple", teacher: { lessons: true } };
    render(<App />);
    await wait(0);
    await wait(0);
    const before = vi.mocked(stubs.api.getDailyPlan).mock.calls.length;
    stubs.api.getQueueRevision = vi.fn(async () => ({ version: 1, revision: 2, updatedAt: null }));
    await wait(REVISION_POLL_MS * 2);
    const after = vi.mocked(stubs.api.getDailyPlan).mock.calls.length;
    expect(after).toBe(before + 1);
    await act(async () => {
      window.dispatchEvent(new Event("focus"));
      await vi.advanceTimersByTimeAsync(0);
    });
    await wait(REVISION_POLL_MS);
    expect(stubs.api.getDailyPlan).toHaveBeenCalledTimes(after);
  });
});

describe("ruling R2: reloads and refetches only where Today's poll ran", () => {
  const OPEN_SESSION = { ...SESSION, checkpoint: null };
  /** A sidecar that holds one completed job and reloads for it on the first read that may. */
  function sidecarWithAJob() {
    const job = { awaiting: false, reloads: 0, revision: 1 };
    stubs.api.getQueueRevision = vi.fn(async (input?: unknown) => {
      const hold = (input as { holdReload?: boolean } | undefined)?.holdReload === true;
      if (job.awaiting && !hold) {
        job.awaiting = false;
        job.reloads += 1;
        return { version: 1, revision: job.revision, updatedAt: null, reloaded: true };
      }
      return { version: 1, revision: job.revision, updatedAt: null };
    });
    return job;
  }
  function planReads() {
    return vi.mocked(stubs.api.getDailyPlan).mock.calls.length;
  }
  async function goto(place: string) {
    fireEvent.click(within(screen.getByRole("navigation", { name: "Places" })).getByRole("button", { name: place }));
    await wait(0);
    await wait(0);
  }
  async function openToday() {
    stubs.session = OPEN_SESSION;
    stubs.config = { shell: "simple", teacher: { lessons: true } };
    render(<App />);
    await wait(0);
    await wait(0);
    expect(screen.getByTestId("today-place-stub")).toBeTruthy();
  }

  it.each(["Library", "Reader"])("a job completed on %s makes no reload; back on Today, one reload and one refetch", async (place) => {
    await openToday();
    const job = sidecarWithAJob();
    await goto(place);
    const before = planReads();
    job.awaiting = true;
    await wait(REVISION_POLL_MS * 4);
    expect(job.reloads).toBe(0);
    expect(planReads()).toBe(before);

    await goto("Today");
    expect(job.reloads).toBe(1);
    expect(planReads()).toBe(before + 1);

    await wait(REVISION_POLL_MS * 3);
    expect(job.reloads).toBe(1);
    expect(planReads()).toBe(before + 1);
  });

  it("a job completed in a lesson makes no reload; closing it, one reload and one refetch", async () => {
    await openToday();
    const job = sidecarWithAJob();
    await act(async () => {
      (stubs.todayProps?.onStartLesson as (entry: unknown) => void)({ kind: "open", entry: "learning_object", learningObjectIds: ["lo_1"], title: "A lesson" });
      await vi.advanceTimersByTimeAsync(0);
    });
    await wait(0);
    expect(screen.getByTestId("lesson-stub")).toBeTruthy();
    const before = planReads();
    job.awaiting = true;
    await wait(REVISION_POLL_MS * 4);
    expect(job.reloads).toBe(0);
    expect(planReads()).toBe(before);

    await act(async () => {
      (stubs.lessonProps?.onClose as () => void)();
      await vi.advanceTimersByTimeAsync(0);
    });
    await wait(0);
    expect(job.reloads).toBe(1);
    expect(planReads()).toBe(before + 1);
  });

  it("a job completed during an exam makes no reload; leaving it, one reload and one refetch", async () => {
    await openToday();
    const job = sidecarWithAJob();
    await act(async () => {
      (stubs.todayProps?.onTakeExam as (goalId: string) => void)("goal_1");
      await vi.advanceTimersByTimeAsync(0);
    });
    await wait(0);
    expect(screen.getByTestId("exam-stub")).toBeTruthy();
    const before = planReads();
    job.awaiting = true;
    await wait(REVISION_POLL_MS * 4);
    expect(job.reloads).toBe(0);
    expect(planReads()).toBe(before);

    await act(async () => {
      (stubs.examProps?.onExit as () => void)();
      await vi.advanceTimersByTimeAsync(0);
    });
    await wait(0);
    expect(job.reloads).toBe(1);
    expect(planReads()).toBe(before + 1);
  });

  it("a phone's revision change on Library refetches nothing, and is paid once on Today", async () => {
    await openToday();
    const job = sidecarWithAJob();
    await goto("Library");
    await wait(REVISION_POLL_MS);
    const before = planReads();
    job.revision = 2;
    await wait(REVISION_POLL_MS * 3);
    expect(planReads()).toBe(before);

    await goto("Today");
    expect(planReads()).toBe(before + 1);
    await wait(REVISION_POLL_MS * 2);
    expect(planReads()).toBe(before + 1);
  });

  it("session_moved is still detected on Library", async () => {
    const seen = renderHook(() => useSessionMoved());
    await openToday();
    const job = sidecarWithAJob();
    await goto("Library");
    await wait(REVISION_POLL_MS);
    job.revision = 2;
    stubs.api.getSession = vi.fn(async () => ({ ...OPEN_SESSION, ownerDeviceId: "dev_phone", ownerLabel: "Phone", ownerGeneration: 1 }));
    await wait(REVISION_POLL_MS);
    expect(stubs.api.getSession).toHaveBeenCalledWith("ses_1");
    expect(seen.result.current?.reason).toBe("adopted");
  });

  it("session_moved is still detected in a lesson", async () => {
    const seen = renderHook(() => useSessionMoved());
    await openToday();
    const job = sidecarWithAJob();
    await act(async () => {
      (stubs.todayProps?.onStartLesson as (entry: unknown) => void)({ kind: "open", entry: "learning_object", learningObjectIds: ["lo_1"], title: "A lesson" });
      await vi.advanceTimersByTimeAsync(0);
    });
    await wait(0);
    await wait(REVISION_POLL_MS);
    job.revision = 2;
    stubs.api.getSession = vi.fn(async () => ({ ...OPEN_SESSION, ownerDeviceId: "dev_phone", ownerLabel: "Phone", ownerGeneration: 1 }));
    await wait(REVISION_POLL_MS);
    expect(seen.result.current?.reason).toBe("adopted");
  });
});
