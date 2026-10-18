// Adaptive difficulty AD1 fix round 5 (V4; spec §5.3 unknown timing,
// G-AD1-10): after a restore, a hint seen earlier whose timing was never
// saved leaves the first-hint marker unknown. Case 4: hints carried back from
// a resumed workbench problem, with no marker and no book. Case 5: a draft
// that saved `hintSeen` (a hint the panel delivered while the marker was not
// recorded) with no counted hint and no marker. A fresh draft still records
// its first hint, and saves `hintSeen` with the draft whatever the switches,
// without changing hintsUsed. Every RPC is a mock.
import type { ComponentProps } from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { setAlgoConfig } from "../app/algoConfig";
import type { WorkbenchSessionDto } from "../api/dto";
import { PracticeScreen } from "./PracticeScreen";

const { api } = vi.hoisted(() => ({ api: {
  getPracticeItem: vi.fn(), getProbeContract: vi.fn(), recoverPracticeSubmission: vi.fn(),
  acknowledgePracticeSubmission: vi.fn(), savePracticeDraft: vi.fn(), submitAttempt: vi.fn(),
  getNextProbeItem: vi.fn(), skipPracticeItem: vi.fn(), submitDontKnow: vi.fn(), stopProbeDiagnosing: vi.fn(),
  recordSelfGradeDisclosure: vi.fn(), recordHintReveal: vi.fn(),
  requestHint: vi.fn(), hintJob: vi.fn(), cancelHint: vi.fn(), answerDiscriminating: vi.fn(), setHelpStyle: vi.fn(),
  workbenchForItem: vi.fn(), workbenchOpen: vi.fn(), workbenchGet: vi.fn(), workbenchReopen: vi.fn(),
  workbenchSaveStep: vi.fn(), workbenchLeave: vi.fn(), workbenchAbandon: vi.fn(), workbenchSubmit: vi.fn(),
  workbenchSetBook: vi.fn(), workbenchRefreshImport: vi.fn(), workbenchBind: vi.fn(), workbenchRetryImport: vi.fn()
} }));
vi.mock("../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../render/MathLiveEditor", () => ({
  MathLiveEditor: (props: { value: string; onChange: (value: string) => void; disabled: boolean; placeholder?: string }) => (
    <textarea aria-label="answer" placeholder={props.placeholder} value={props.value} disabled={props.disabled}
      onChange={(event) => props.onChange(event.target.value)} />
  )
}));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));
vi.mock("../components/CardControls", () => ({ CardControls: () => <span>card controls</span> }));
vi.mock("../render/LiveMarkdownEditor", () => ({
  LiveMarkdownEditor: (p: { value: string; onChange: (value: string) => void; ariaLabel?: string }) => (
    <textarea aria-label={p.ariaLabel} value={p.value} onChange={(event) => p.onChange(event.target.value)} />
  )
}));

const ITEM_ID = "pi_ad1";
const AD_ON = { ratingTap: false, firstHintProgress: true };

function item() {
  return {
    id: ITEM_ID, learningObjectId: "lo_det", learningObjectTitle: "Determinants", subject: "linear_algebra",
    subjects: ["linear_algebra"], practiceMode: "constructed_response", attemptTypesAllowed: ["independent_attempt", "hinted_attempt"],
    presentation: { practiceItemId: ITEM_ID, blocks: [{ kind: "prompt", markdown: "Compute det(A).", label: null }] },
    prompt: "Compute det(A).", expectedAnswer: "det(A) = -3.",
    hints: ["Start with the first row.", "Watch the signs.", "Add the terms."],
    hintPolicy: { maxUsefulHints: 3 }, candidateErrorTypes: [], tags: [], sourceRefs: [],
    attempts: [], evidenceFacets: [], evidenceWeights: {},
    rubric: { maxPoints: 4, criteria: [{ id: "value", description: "Gets -3", points: 4 }], fatalErrors: [] },
    mastery: { mean: 0.5, variance: 0.18 }, elicitation: null
  };
}

function wb(overrides: Partial<WorkbenchSessionDto> = {}): WorkbenchSessionDto {
  return {
    sessionId: "wb_old", practiceItemId: ITEM_ID, stemMd: "Compute det(A).", importStatus: "none", importError: null,
    origin: "practice", entry: "practice_screen", parentSessionId: null, extractionId: null, spanIds: [],
    sourceVisible: false, sourceHiddenAt: null, sourceShownAt: null, practiceSessionId: null, helpStyle: null,
    status: "open", attemptId: null, createdAt: "x", updatedAt: "x", closedAt: null, steps: [], lastEditedStepId: null,
    parts: null, sourceId: null,
    record: { bookCounted: false, bookVisible: false, hints: 1, questionHints: 0, ownAttempt: false, line: "a hint",
              footer: "book hidden · help used: 1 hint", stuckNote: null },
    ...overrides
  };
}

function props(overrides: Partial<ComponentProps<typeof PracticeScreen>> = {}): ComponentProps<typeof PracticeScreen> {
  return {
    session: { sessionId: "s1" } as ComponentProps<typeof PracticeScreen>["session"],
    practiceItemId: ITEM_ID, gradingReady: true, gradingProvider: "codex",
    onFeedback: vi.fn(), onBlockEnd: vi.fn(), onContinueDiagnostic: vi.fn(), onBack: vi.fn(),
    onCheckpointCleared: vi.fn(), onDraftSaved: vi.fn(), onTeachBackActive: vi.fn(),
    onAskAvailabilityChange: vi.fn(), onInspect: vi.fn(), onAsk: vi.fn(), onError: vi.fn(),
    ...overrides
  };
}

function pressHint() {
  fireEvent.keyDown(window, { key: "h", ctrlKey: true });
}

async function submitted() {
  fireEvent.click(screen.getByRole("button", { name: /Submit/ }));
  await waitFor(() => expect(api.submitAttempt).toHaveBeenCalledOnce());
  return api.submitAttempt.mock.calls[0][0];
}

function savedMarkers() {
  return api.savePracticeDraft.mock.calls.map(([draft]) => draft.firstHintProgress ?? null);
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  api.getPracticeItem.mockResolvedValue(item());
  api.getProbeContract.mockResolvedValue({ version: 1, active: false });
  api.savePracticeDraft.mockResolvedValue({});
  api.acknowledgePracticeSubmission.mockResolvedValue({ acknowledged: true });
  api.recoverPracticeSubmission.mockResolvedValue({ status: "pending", result: null });
  api.recordHintReveal.mockResolvedValue({ version: 1, recorded: true, reason: null, assistId: "ha_1" });
  api.submitAttempt.mockResolvedValue({ attemptId: "att-1", learningObjectId: "lo_det", probeEpisode: { feedbackDeferred: false } });
  api.workbenchForItem.mockResolvedValue({ sessions: [] });
  api.workbenchOpen.mockResolvedValue({ session: wb(), resumed: false });
  api.workbenchLeave.mockResolvedValue({ session: wb() });
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  const stored = new Map<string, string>();
  Object.defineProperty(window, "localStorage", {
    configurable: true,
    value: {
      getItem: (key: string) => stored.get(key) ?? null,
      setItem: (key: string, value: string) => void stored.set(key, String(value)),
      removeItem: (key: string) => void stored.delete(key),
      clear: () => stored.clear()
    }
  });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  setAlgoConfig(undefined);
});

it("case 4: hints carried back from resumed steps, with no marker, leave a later reveal unmarked", async () => {
  setAlgoConfig({ ui: { practiceFeedback: "classic" }, adaptiveDifficulty: AD_ON,
                  workbench: { enabled: true, openSessionDays: 30 } });
  api.workbenchForItem.mockResolvedValue({ sessions: [{ sessionId: "wb_old", status: "open", stepCount: 1 }] });
  api.workbenchOpen.mockResolvedValue({ resumed: true, session: wb({ carriedHints: 1 }) });
  render(<PracticeScreen {...props({ restoredSubmissionId: "k1" })} />);
  fireEvent.click(await screen.findByRole("button", { name: "resume your steps" }));
  await screen.findByRole("region", { name: "workbench" });
  fireEvent.click(screen.getByRole("button", { name: "answer box instead" }));
  const answer = await screen.findByRole("textbox", { name: "answer" });
  fireEvent.change(answer, { target: { value: "expand along row 1" } });
  pressHint();
  await screen.findByText("Watch the signs.");
  const payload = await submitted();
  expect(payload).not.toHaveProperty("firstHintProgress");
  expect(savedMarkers().every((marker) => marker === null)).toBe(true);
});

it("case 5: a draft that saved hintSeen, with no counted hint and no marker, leaves the panel's delivery unmarked", async () => {
  setAlgoConfig({ ui: { practiceFeedback: "classic" }, adaptiveDifficulty: AD_ON,
                  hints: { adaptiveEnabled: true, authoredOfferAfterSeconds: 4, helpStyle: "balanced" } });
  api.requestHint.mockResolvedValue({ version: 1, jobId: "hjob_1", state: "done", result: {
    status: "ready", assistId: "ha_1", hintMd: "Evaluate the determinant row by row.", kind: "next_step", level: 3,
    labels: { origin: "AI-written", kind: "the next step", workedHelp: null, horizon: null },
    evidence: { countsAsHint: true, primed: false, level: 3 }, replies: [], picks: [], shown: true
  } });
  render(<PracticeScreen {...props({ restoredAnswer: "expand along row 1", restoredHints: 0, restoredSubmissionId: "k1",
                                      restoredHintSeen: true })} />);
  await screen.findByRole("textbox", { name: "answer" });
  pressHint();
  await screen.findByText("Evaluate the determinant row by row.");
  const payload = await submitted();
  expect(payload).not.toHaveProperty("firstHintProgress");
  expect(savedMarkers().every((marker) => marker === null)).toBe(true);
});

it("a fresh draft records its first hint and saves hintSeen, with hintsUsed unchanged", async () => {
  setAlgoConfig({ ui: { practiceFeedback: "classic" }, adaptiveDifficulty: AD_ON });
  render(<PracticeScreen {...props()} />);
  await screen.findByRole("textbox", { name: "answer" });
  await waitFor(() => expect(api.getProbeContract).toHaveBeenCalled());
  pressHint();
  await screen.findByText("Start with the first row.");
  await waitFor(() => expect(api.savePracticeDraft).toHaveBeenCalledWith(
    expect.objectContaining({ hintSeen: true, hintsUsed: 1, firstHintProgress: "no_draft" })));
  const payload = await submitted();
  expect(payload.firstHintProgress).toBe("no_draft");
  expect(payload.hintsUsed).toBe(1);
});

it("with the marker off, a hint still saves hintSeen, so turning it on later knows the timing is unknown", async () => {
  setAlgoConfig({ ui: { practiceFeedback: "classic" } });
  render(<PracticeScreen {...props()} />);
  await screen.findByRole("textbox", { name: "answer" });
  await waitFor(() => expect(api.getProbeContract).toHaveBeenCalled());
  pressHint();
  await screen.findByText("Start with the first row.");
  await waitFor(() => expect(api.savePracticeDraft).toHaveBeenCalledWith(expect.objectContaining({ hintSeen: true })));
  for (const [draft] of api.savePracticeDraft.mock.calls) expect(draft).not.toHaveProperty("firstHintProgress");
});
