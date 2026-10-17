// RW2a on the practice screen (spec §5.1, D9; UX §5.12): a remembered "Work in
// steps" button, not the default answer surface, opens the same step editor
// full width with the item's stem on top and no book; the item's practice card
// offers "resume your steps" for an open problem; Submit goes through the
// workbench's ordinary submit with the serve's own offer and presentation and
// lands on feedback; a diagnostic check never offers it.
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
vi.mock("../components/ItemPresentation", () => ({ ItemPresentation: () => <p>Question</p> }));
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

it("offers Work in steps beside the answer box, never instead of it", async () => {
  render(<PracticeScreen {...props()} />);
  expect(await screen.findByRole("textbox", { name: "answer" })).toBeTruthy();
  expect(await screen.findByRole("button", { name: /work in steps/i })).toBeTruthy();
  expect(screen.queryByRole("region", { name: "workbench" })).toBeNull();
});

it("Work in steps opens the step editor full width with the stem on top and no book", async () => {
  render(<PracticeScreen {...props()} />);
  fireEvent.click(await screen.findByRole("button", { name: /work in steps/i }));
  await waitFor(() => expect(api.workbenchOpen).toHaveBeenCalledWith(expect.objectContaining({
    origin: "practice", entry: "practice_screen", practiceItemId: "pi_1", stemMd: PROMPT,
  })));
  const pane = await screen.findByRole("region", { name: "workbench" });
  expect(pane.closest("[data-workbench-pane]")?.getAttribute("data-layout")).toBe("full");
  expect(screen.queryByRole("textbox", { name: "answer" })).toBeNull();
  expect(screen.queryByRole("radiogroup", { name: "the book while you work" })).toBeNull();
  expect(screen.getByRole("textbox", { name: "Step 1" })).toBeTruthy();
});

it("the choice is remembered on this device, and the answer box is one click back", async () => {
  const first = render(<PracticeScreen {...props()} />);
  fireEvent.click(await screen.findByRole("button", { name: /work in steps/i }));
  await screen.findByRole("region", { name: "workbench" });
  first.unmount();
  render(<PracticeScreen {...props()} />);
  expect(await screen.findByRole("region", { name: "workbench" })).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "answer box instead" }));
  expect(await screen.findByRole("textbox", { name: "answer" })).toBeTruthy();
  expect(window.localStorage.getItem("ll.workbench.workInSteps")).toBeNull();
});

it("the practice card offers to resume an open problem's steps, or reopen a set-aside one", async () => {
  api.workbenchForItem.mockResolvedValue({ sessions: [{ sessionId: "wb_old", status: "open", stepCount: 3 }] });
  api.workbenchGet.mockResolvedValue({ session: wb({ sessionId: "wb_old", steps: [
    { stepId: "a", chainId: "a", ordinal: 1, kind: "step", bodyMd: "U Sigma", deleted: false, createdAt: "x", editedAt: "x", versions: [] },
  ] }) });
  const view = render(<PracticeScreen {...props()} />);
  fireEvent.click(await screen.findByRole("button", { name: "resume your steps" }));
  await waitFor(() => expect(api.workbenchGet).toHaveBeenCalledWith({ sessionId: "wb_old" }));
  expect(((await screen.findByRole("textbox", { name: "Step 1" })) as HTMLTextAreaElement).value).toBe("U Sigma");
  view.unmount();
  window.localStorage.clear();
  api.workbenchForItem.mockResolvedValue({ sessions: [{ sessionId: "wb_old", status: "abandoned", stepCount: 3 }] });
  api.workbenchReopen.mockResolvedValue({ session: wb({ sessionId: "wb_old" }) });
  render(<PracticeScreen {...props()} />);
  fireEvent.click(await screen.findByRole("button", { name: "reopen your steps" }));
  await waitFor(() => expect(api.workbenchReopen).toHaveBeenCalledWith({ sessionId: "wb_old" }));
});

it("Submit in steps uses this serve's offer and presentation and lands on feedback", async () => {
  api.workbenchOpen.mockResolvedValue({ session: wb({ steps: [
    { stepId: "a", chainId: "a", ordinal: 1, kind: "step", bodyMd: "A = U Sigma V^T", deleted: false, createdAt: "x", editedAt: "x", versions: [] },
  ] }), resumed: false });
  api.workbenchSubmit.mockResolvedValue({ version: 1, attempt: { attemptId: "att_9" }, session: wb({ status: "submitted", attemptId: "att_9" }), practiceSession: { sessionId: "s1" } });
  const callbacks = props({ planPresentationId: "pres_1" });
  render(<PracticeScreen {...callbacks} />);
  fireEvent.click(await screen.findByRole("button", { name: /work in steps/i }));
  await waitFor(() => expect(api.workbenchOpen).toHaveBeenCalledWith(expect.objectContaining({ origin: "plan", entry: "plan" })));
  fireEvent.click(await screen.findByRole("button", { name: /^submit/ }));
  await waitFor(() => expect(api.workbenchSubmit).toHaveBeenCalledWith(expect.objectContaining({
    sessionId: "wb_p", practiceSessionId: "s1", schedulerCandidateId: "cand_1", planPresentationId: "pres_1",
  })));
  await waitFor(() => expect(callbacks.onFeedback).toHaveBeenCalledWith("att_9"));
  expect(api.submitAttempt).not.toHaveBeenCalled();
});

it("a diagnostic check never offers Work in steps", async () => {
  api.getProbeContract.mockResolvedValue({
    version: 1, active: true, presentationId: "pres_probe", forcedAttemptType: "diagnostic_probe",
    restrictions: { hintsDisabled: true, askTutorDisabled: true, workedExampleDisabled: true, answerRevealDisabled: true, feedbackDeferred: true },
  });
  render(<PracticeScreen {...props()} />);
  await screen.findByRole("textbox", { name: "answer" });
  expect(screen.queryByRole("button", { name: /work in steps/i })).toBeNull();
  expect(api.workbenchForItem).not.toHaveBeenCalled();
});
