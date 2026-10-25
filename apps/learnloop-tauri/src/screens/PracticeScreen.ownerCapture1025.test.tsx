// Owner capture 2026-10-25 (docs/reviews/owner-capture-2026-10-25-fixes.md),
// the practice screen in "Work in steps". B1: Ask works there (a button, the
// `?` key) and carries the steps as the learner's work. B3/B4: a steps submit
// supersedes the answer box's draft: it is never saved again on unmount and
// App's mirror of it is cleared, so the item served again starts fresh
// (no restored retry key, hints or offer binding).
import type { ComponentProps } from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { PracticeScreen } from "./PracticeScreen";
import { setAlgoConfig } from "../app/algoConfig";
import type { WorkbenchSessionDto } from "../api/dto";

const { api } = vi.hoisted(() => ({ api: {
  getPracticeItem: vi.fn(), getProbeContract: vi.fn(), recoverPracticeSubmission: vi.fn(),
  acknowledgePracticeSubmission: vi.fn(), savePracticeDraft: vi.fn(), submitAttempt: vi.fn(),
  getNextProbeItem: vi.fn(), startTeachBack: vi.fn(), submitTeachBackTurn: vi.fn(),
  placementSelfReport: vi.fn(), submitDontKnow: vi.fn(),
  workbenchForItem: vi.fn(), workbenchOpen: vi.fn(), workbenchGet: vi.fn(), workbenchReopen: vi.fn(),
  workbenchSaveStep: vi.fn(), workbenchLeave: vi.fn(), workbenchAbandon: vi.fn(), workbenchSubmit: vi.fn(),
  workbenchSetBook: vi.fn(), workbenchRefreshImport: vi.fn(), workbenchBind: vi.fn(), workbenchRetryImport: vi.fn(),
} }));
vi.mock("../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../render/MathLiveEditor", () => ({ MathLiveEditor: (props: { value: string; onChange: (value: string) => void; disabled: boolean }) => <textarea aria-label="answer" role="textbox" value={props.value} disabled={props.disabled} onChange={(event) => props.onChange(event.target.value)} /> }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../components/ItemPresentation", () => ({
  ItemPresentation: ({ presentation }: { presentation?: { blocks?: Array<{ markdown: string }> } }) => (
    <p data-testid="item-presentation">{presentation?.blocks?.map((block) => block.markdown).join(" | ") || "Question"}</p>
  ),
}));
vi.mock("../render/LiveMarkdownEditor", () => ({
  LiveMarkdownEditor: (p: { value: string; onChange: (value: string) => void; ariaLabel?: string }) => (
    <textarea aria-label={p.ariaLabel} value={p.value} onChange={(event) => p.onChange(event.target.value)} />
  ),
}));

const PROMPT = "Write the SVD of A.";

function wb(overrides: Partial<WorkbenchSessionDto> = {}): WorkbenchSessionDto {
  return {
    sessionId: "wb_p", practiceItemId: "pi_1", stemMd: PROMPT, importStatus: "none", importError: null, origin: "practice",
    entry: "practice_screen", parentSessionId: null, extractionId: null, spanIds: [], sourceVisible: false, sourceHiddenAt: null,
    sourceShownAt: null, practiceSessionId: null, helpStyle: null, status: "open", attemptId: null, createdAt: "x",
    updatedAt: "x", closedAt: null, steps: [], lastEditedStepId: null, parts: null, sourceId: null,
    record: { bookCounted: false, bookVisible: false, hints: 0, questionHints: 0, ownAttempt: true, line: "your own attempt", footer: "book hidden · help used: none", stuckNote: null },
    ...overrides,
  };
}

function props(overrides: Partial<ComponentProps<typeof PracticeScreen>> = {}): ComponentProps<typeof PracticeScreen> {
  return {
    session: { sessionId: "s1" } as ComponentProps<typeof PracticeScreen>["session"],
    practiceItemId: "pi_1", schedulerCandidateId: "cand_1", gradingReady: true, gradingProvider: "fake",
    onFeedback: vi.fn(), onBlockEnd: vi.fn(), onContinueDiagnostic: vi.fn(), onBack: vi.fn(),
    onCheckpointCleared: vi.fn(), onDraftSaved: vi.fn(), onTeachBackActive: vi.fn(),
    onAskAvailabilityChange: vi.fn(), onInspect: vi.fn(), onAsk: vi.fn(), onError: vi.fn(),
    ...overrides,
  };
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  // jsdom's storage is shadowed in this Node; give the screen a real one.
  const store = new Map<string, string>();
  Object.defineProperty(window, "localStorage", {
    configurable: true,
    value: {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => void store.set(k, String(v)),
      removeItem: (k: string) => void store.delete(k),
      clear: () => store.clear(),
    },
  });
  setAlgoConfig({ workbench: { enabled: true, openSessionDays: 30 } });
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  api.getPracticeItem.mockResolvedValue({
    id: "pi_1", learningObjectId: "lo", learningObjectTitle: "Topic", practiceMode: "open_text", prompt: PROMPT,
    attemptTypesAllowed: ["independent_attempt"], evidenceFacets: [], evidenceWeights: {}, hints: [],
    hintPolicy: { maxUsefulHints: 0 }, candidateErrorTypes: [], tags: [], sourceRefs: [], attempts: [], rubric: null,
  });
  api.getProbeContract.mockResolvedValue({ version: 1, active: false });
  api.savePracticeDraft.mockResolvedValue({});
  api.workbenchForItem.mockResolvedValue({ sessions: [] });
  api.workbenchOpen.mockResolvedValue({ session: wb(), resumed: false });
  api.workbenchLeave.mockResolvedValue({ session: wb() });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); });


const STEP = { stepId: "a", chainId: "a", ordinal: 1, kind: "step" as const, bodyMd: "A = U Sigma V^T", deleted: false, createdAt: "x", editedAt: "x", versions: [] };

async function intoSteps(callbacks: ComponentProps<typeof PracticeScreen>) {
  api.workbenchOpen.mockResolvedValue({ session: wb({ steps: [STEP] }), resumed: false });
  render(<PracticeScreen {...callbacks} />);
  fireEvent.click(await screen.findByRole("button", { name: /work in steps/i }));
  return screen.findByRole("region", { name: "workbench" });
}

it("B1: Ask is offered in steps and opens the tutor with the steps as the work", async () => {
  const callbacks = props();
  await intoSteps(callbacks);
  fireEvent.click(await screen.findByRole("button", { name: /^ask/ }));
  expect(callbacks.onAsk).toHaveBeenCalledWith(expect.objectContaining({
    context: "practice", practiceItemId: "pi_1", sessionId: "s1", attemptProgress: "draft_started",
    workMd: "1. A = U Sigma V^T",
  }));
});

it("B1: the ? key opens Ask in steps when no step has the caret", async () => {
  const callbacks = props();
  const region = await intoSteps(callbacks);
  fireEvent.keyDown(region, { key: "?" });
  expect(callbacks.onAsk).toHaveBeenCalledTimes(1);
  // Typed in a step, ? is the learner's text.
  fireEvent.keyDown(screen.getByRole("textbox", { name: "Step 1" }), { key: "?" });
  expect(callbacks.onAsk).toHaveBeenCalledTimes(1);
});

it("B1: the command palette's Ask reads the steps too", async () => {
  let reader: (() => { workMd?: string; attemptProgress: string }) | null = null;
  const callbacks = props({ onAskState: (next) => { reader = next; } });
  await intoSteps(callbacks);
  await waitFor(() => expect(reader?.().workMd).toBe("1. A = U Sigma V^T"));
  expect(reader!().attemptProgress).toBe("draft_started");
});

it("B3/B4: a steps submit supersedes the answer box's draft", async () => {
  api.workbenchSubmit.mockResolvedValue({ version: 1, attempt: { attemptId: "att_9" }, session: wb({ status: "submitted", attemptId: "att_9" }), practiceSession: { sessionId: "s1" } });
  api.recoverPracticeSubmission.mockResolvedValue({ version: 1, status: "pending", result: null });
  const callbacks = props({ restoredSubmissionId: "box-key" });
  await intoSteps(callbacks);
  fireEvent.click(await screen.findByRole("button", { name: /^submit/ }));
  await waitFor(() => expect(callbacks.onFeedback).toHaveBeenCalledWith("att_9"));
  expect(callbacks.onCheckpointCleared).toHaveBeenCalledWith({ practiceItemId: "pi_1", submissionId: "box-key" });
  const saves = api.savePracticeDraft.mock.calls.length;
  cleanup();
  // Unmounting (feedback replaces the screen) saves no draft and mirrors none.
  expect(api.savePracticeDraft.mock.calls.length).toBe(saves);
  expect(callbacks.onDraftSaved).not.toHaveBeenCalled();
});
