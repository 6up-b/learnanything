// Reader CA2 (docs/specs/ux_reader_compare_ask_v1.md §7; docs/reviews/reader-ca2-one-ask.md),
// the practice screen with the one Ask panel on (the sidecar's `ask` key):
// Ask docks beside the question (never the overlay), asks inline under the
// focused step in Work in Steps, keeps one help record, counts an earlier
// attempt's help opened before Submit once, changes the cold banner only after
// a question about the maths, and offers the take step on a cold follow-up the
// server serves with it (Q4) instead of "No hints on this one".
import type { ComponentProps } from "react";
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { PracticeScreen, helpRecordLine } from "./PracticeScreen";
import { setAlgoConfig } from "../app/algoConfig";
import type { WorkbenchSessionDto } from "../api/dto";

const { api } = vi.hoisted(() => ({ api: {
  getPracticeItem: vi.fn(), getProbeContract: vi.fn(), recoverPracticeSubmission: vi.fn(),
  acknowledgePracticeSubmission: vi.fn(), savePracticeDraft: vi.fn(), submitAttempt: vi.fn(),
  getNextProbeItem: vi.fn(), startTeachBack: vi.fn(), submitTeachBackTurn: vi.fn(),
  getTutorTranscript: vi.fn(), askTutorQuestion: vi.fn(), getLearnerTextGap: vi.fn(), setHelpStyle: vi.fn(),
  recordHintReveal: vi.fn(),
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
const EARLIER = [{
  attemptId: "att_old", at: "2026-10-14T10:00:00Z",
  outcome: { label: "with help ◌", assisted: true, rubricScore: 2, maxPoints: 4 },
  exchanges: [{ eventId: "q_old", context: "practice", questionMd: "an old question", answerMd: "an old answer",
                questionType: "mechanism", hintEquivalent: true, createdAt: "2026-10-14T09:59:00Z" }],
  hints: []
}];

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
  setAlgoConfig({ workbench: { enabled: true, openSessionDays: 30 }, ui: { practiceFeedback: "simple" },
                  ask: { panelEnabled: true, helpStyle: "balanced", coldHelpConverts: true } });
  api.getTutorTranscript.mockResolvedValue({ events: [], remaining: 3, earlier: EARLIER, earlierCountsAsHint: true, cold: false });
  api.askTutorQuestion.mockResolvedValue({
    version: 1, eventId: "q1", answerMd: "Think of the shapes.", questionType: "clarification", facets: [],
    hintEquivalent: false, leakSuspected: false, citations: [], remaining: 2, answerMode: "help_me_reason",
  });
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

async function ask(text: string) {
  const input = screen.getByRole("textbox", { name: "ask in your words" });
  fireEvent.change(input, { target: { value: text } });
  fireEvent.keyDown(input, { key: "Enter" });
  await waitFor(() => expect(api.askTutorQuestion).toHaveBeenCalled());
  return api.askTutorQuestion.mock.calls[api.askTutorQuestion.mock.calls.length - 1][0];
}

it("Ask docks beside the question with the attempt's key and the live draft, never the overlay", async () => {
  api.recoverPracticeSubmission.mockResolvedValue({ version: 1, status: "pending", result: null });
  const callbacks = props({ restoredSubmissionId: "serve-key" });
  render(<PracticeScreen {...callbacks} />);
  fireEvent.change(await screen.findByRole("textbox", { name: "answer" }), { target: { value: "A = U S V^T" } });
  fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));
  expect(await screen.findByTestId("ask-panel-docked")).toBeTruthy();
  expect(screen.getByTestId("ask-dock")).toBeTruthy();
  expect(callbacks.onAsk).not.toHaveBeenCalled();
  // The draft beside it is still on screen and still editable.
  fireEvent.change(screen.getByRole("textbox", { name: "answer" }), { target: { value: "A = U S V^T, S diagonal" } });
  const payload = await ask("What does S hold?");
  expect(payload).toMatchObject({ context: "practice", submissionId: "serve-key", learnerDraftMd: "A = U S V^T, S diagonal" });
  await waitFor(() => expect(screen.getByTestId("help-record").textContent).toBe("help used: a clarification (free)"));
});

it("the palette's Ask opens the panel through the screen's opener", async () => {
  let opener: (() => void) | null = null;
  render(<PracticeScreen {...props({ onAskOpener: (next) => { opener = next; } })} />);
  await screen.findByRole("textbox", { name: "answer" });
  await waitFor(() => expect(opener).not.toBeNull());
  act(() => opener!());
  expect(await screen.findByTestId("ask-panel-docked")).toBeTruthy();
});

it("an earlier attempt's help opened before Submit counts once, on the draft, never in the client's count (Codex F1)", async () => {
  api.submitAttempt.mockResolvedValue({ version: 1, attemptId: "att_1" });
  api.recoverPracticeSubmission.mockResolvedValue({ version: 1, status: "pending", result: null });
  render(<PracticeScreen {...props()} />);
  fireEvent.change(await screen.findByRole("textbox", { name: "answer" }), { target: { value: "my answer" } });
  fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));
  const foot = await screen.findByTestId("ask-earlier");
  fireEvent.click(within(foot).getByRole("button", { name: /earlier on this question/ }));
  fireEvent.click(within(foot).getByRole("button", { name: /earlier on this question/ }));
  fireEvent.click(within(foot).getByRole("button", { name: /earlier on this question/ }));
  await waitFor(() => expect(screen.getByTestId("help-record").textContent).toBe(
    "help used: an earlier attempt's help (counts as a hint)"));
  fireEvent.click(screen.getByRole("button", { name: /submit/i }));
  await waitFor(() => expect(api.submitAttempt).toHaveBeenCalled());
  // Codex review F1: recorded on the draft (its checkpoint), counted by the
  // submit's server side whatever surface submits and after a restart.
  expect(api.savePracticeDraft.mock.calls.some(([draft]) => draft.earlierOpened === true)).toBe(true);
  const submitted = api.submitAttempt.mock.calls[0][0];
  expect(submitted.hintsUsed).toBe(0);
  expect(submitted.authoredHints).toBe(0);
});

it("the help record is the server's after a remount, and an earlier opening is restored (Codex F1, F7)", async () => {
  api.recoverPracticeSubmission.mockResolvedValue({ version: 1, status: "pending", result: null });
  api.getTutorTranscript.mockResolvedValue({
    events: [], remaining: null, earlier: EARLIER, earlierCountsAsHint: true, cold: false,
    helpRecord: { counted: 2, earlierOpened: true, items: [
      { kind: "question", at: "2026-10-25T10:00:00Z", counts: true, thisAttempt: false, eventId: "q_prev" },
      { kind: "earlier", at: null, counts: true },
    ] },
  });
  render(<PracticeScreen {...props({ restoredSubmissionId: "serve-2" })} />);
  await waitFor(() => expect(screen.getByTestId("help-record").textContent).toBe(
    "help used: a question from before this serve (counts as a hint) · an earlier attempt's help (counts as a hint)"));
  fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));
  const foot = await screen.findByTestId("ask-earlier");
  await waitFor(() => expect(foot.textContent).toContain("opened · counted as a hint"));
  fireEvent.click(within(foot).getByRole("button", { name: /earlier on this question/ }));
  // Already counted: opening it again saves nothing new.
  expect(api.savePracticeDraft.mock.calls.some(([draft]) => draft.earlierOpened === true)).toBe(false);
});

it("in steps, Ask opens inline under the focused step, about that step", async () => {
  api.workbenchOpen.mockResolvedValue({ session: wb({ steps: [STEP] }), resumed: false });
  const callbacks = props();
  render(<PracticeScreen {...callbacks} />);
  fireEvent.click(await screen.findByRole("button", { name: /work in steps/i }));
  const region = await screen.findByRole("region", { name: "workbench" });
  fireEvent.focus(screen.getByRole("textbox", { name: "Step 1" }));
  fireEvent.keyDown(region, { key: "?" });
  const inline = await screen.findByTestId("workbench-step-ask");
  expect(callbacks.onAsk).not.toHaveBeenCalled();
  expect(screen.queryByTestId("ask-panel-docked")).toBeNull();
  const input = within(inline).getByRole("textbox", { name: "ask about step 1" });
  fireEvent.change(input, { target: { value: "why this order?" } });
  fireEvent.keyDown(input, { key: "Enter" });
  await waitFor(() => expect(api.askTutorQuestion).toHaveBeenCalledOnce());
  expect(api.askTutorQuestion.mock.calls[0][0]).toMatchObject({
    workbenchSessionId: "wb_p", aboutStep: 1, learnerDraftMd: "1. A = U Sigma V^T"
  });
  expect(screen.getByRole("button", { name: /ask about this step/ })).toBeTruthy();
});

const COLD_ITEM = {
  activeFollowupKind: "cold_retry", hints: ["Think about orthogonality."],
  intentCheck: { kind: "cold_followup", cold: true, banner: "A check on your own. Help is still here — using it makes this practice with help.",
                 helpHeader: "Taking any help makes this attempt practice with help, not a check on your own.",
                 locatorsHidden: true, restoration: null },
};

async function coldItem(item: Record<string, unknown>) {
  const base = await api.getPracticeItem.getMockImplementation()?.();
  api.getPracticeItem.mockResolvedValue({ ...(base ?? {}), id: "pi_1", learningObjectId: "lo", learningObjectTitle: "Topic",
    practiceMode: "open_text", prompt: PROMPT, attemptTypesAllowed: ["independent_attempt", "hinted_attempt"],
    evidenceFacets: [], evidenceWeights: {}, hintPolicy: { maxUsefulHints: 3 }, candidateErrorTypes: [], tags: [],
    sourceRefs: [], attempts: [], rubric: null, ...item });
}

it("Q4: a cold follow-up served with the take step offers help instead of 'No hints on this one'", async () => {
  await coldItem(COLD_ITEM);
  const callbacks = props();
  render(<PracticeScreen {...callbacks} />);
  expect(await screen.findByTestId("intent-check-banner")).toBeTruthy();
  expect(screen.queryByText(/no hints on this one/i)).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: /^hint$/i }));
  expect(callbacks.onError).not.toHaveBeenCalledWith("No hints on this one: it's a check on your own.");
});

it("without the take step (the predecessor), a cold follow-up still withholds hints", async () => {
  await coldItem({ activeFollowupKind: "cold_retry", hints: ["Think about orthogonality."] });
  render(<PracticeScreen {...props()} />);
  expect(await screen.findByText(/no hints on this one/i)).toBeTruthy();
  expect(screen.queryByRole("button", { name: /^hint$/i })).toBeNull();
});

it("§7.7: the banner changes only after a question about the maths", async () => {
  await coldItem(COLD_ITEM);
  render(<PracticeScreen {...props()} />);
  const banner = await screen.findByTestId("intent-check-banner");
  fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));
  await screen.findByTestId("ask-panel-docked");
  await ask("What does sigma mean?");
  await waitFor(() => expect(screen.getByTestId("ask-answer-label").textContent).toContain("still on your own"));
  expect(banner.textContent).toContain("A check on your own");
  api.askTutorQuestion.mockResolvedValue({
    version: 1, eventId: "q2", answerMd: "Orthogonal columns.", questionType: "mechanism", facets: [],
    hintEquivalent: true, leakSuspected: false, citations: [], remaining: 1, answerMode: "help_me_reason",
  });
  await ask("Why are the columns orthogonal?");
  await waitFor(() => expect(screen.getByTestId("intent-check-banner").textContent).toBe(
    "Practice with help ◌ — you asked about the maths"));
});

it("re-review F14: worked help is never also a phantom hint; entries reconcile with the record by identity", () => {
  const worked = { kind: "worked" as const, at: "2026-10-25T10:00:00Z", counts: false, level: 4, countedBy: "server" as const,
                   assistId: "ha_worked" };
  const server = { items: [worked], counted: 0, earlierOpened: false };
  // One L4 entry: the server's own row, listed once as worked help.
  expect(helpRecordLine({ hints: 1, entries: [{ assistId: "ha_worked", level: 4 }], book: false, earlier: false,
                          questions: [], server }))
    .toBe("help used: worked help (L4) · practice with help");
  // An authored hint the server has no row for is the screen's own hint.
  expect(helpRecordLine({ hints: 2, entries: [{ assistId: "ha_worked", level: 4 }, { assistId: null, level: 3 }],
                          book: false, earlier: false, questions: [], server }))
    .toBe("help used: a hint · worked help (L4) · practice with help");
  // A worked entry the record has not read back yet is still worked help, not a hint.
  expect(helpRecordLine({ hints: 1, entries: [{ assistId: "ha_new", level: 5 }], book: false, earlier: false,
                          questions: [], server: { items: [], counted: 0, earlierOpened: false } }))
    .toBe("help used: worked help (L5) · practice with help");
  // A server L2 hint the screen also holds counts once.
  const hint = { kind: "hint" as const, at: "2026-10-25T10:00:00Z", counts: true, level: 2, countedBy: "server" as const,
                 assistId: "ha_hint" };
  expect(helpRecordLine({ hints: 1, entries: [{ assistId: "ha_hint", level: 2 }], book: false, earlier: false,
                          questions: [], server: { items: [hint], counted: 1, earlierOpened: false } }))
    .toBe("help used: a hint (L2)");
});

it("fix round F14: without the record, the screen's entries are classified by level too", () => {
  // The transcript could not be read: L4-L5 entries are worked help, never "a hint".
  expect(helpRecordLine({ hints: 1, entries: [{ assistId: "h4", level: 4 }], book: false, earlier: false,
                          questions: [], server: null }))
    .toBe("help used: worked help (L4) · practice with help");
  expect(helpRecordLine({ hints: 2, entries: [{ assistId: "h4", level: 4 }, { assistId: "h2", level: 2 }], book: false,
                          earlier: false, questions: [], server: null }))
    .toBe("help used: a hint · worked help (L4) · practice with help");
  // Without adaptive hints (no entries) the line is today's.
  expect(helpRecordLine({ hints: 1, book: false, earlier: false, questions: [], server: null }))
    .toBe("help used: a hint");
});

it("fix round F15: an earlier opening carried into steps comes back as itself, never as an authored hint", async () => {
  api.recoverPracticeSubmission.mockResolvedValue({ version: 1, status: "pending", result: null });
  api.getTutorTranscript.mockResolvedValue({ events: [], remaining: 3, earlier: EARLIER, earlierCountsAsHint: true, cold: false });
  const base = await api.getPracticeItem.getMockImplementation()?.();
  api.getPracticeItem.mockResolvedValue({ ...(base ?? {}), id: "pi_1", learningObjectId: "lo", learningObjectTitle: "Topic",
    practiceMode: "open_text", prompt: PROMPT, attemptTypesAllowed: ["independent_attempt", "hinted_attempt"],
    evidenceFacets: [], evidenceWeights: {}, hints: ["Start from A^T A."], hintPolicy: { maxUsefulHints: 2 },
    candidateErrorTypes: [], tags: [], sourceRefs: [], attempts: [], rubric: null });
  // The server holds the opening on the problem (a draft from before a
  // restart opened it); no authored hint was revealed.
  api.workbenchOpen.mockResolvedValue({ session: wb({ carriedHints: 0, earlierOpened: true }), resumed: true });
  render(<PracticeScreen {...props({ restoredSubmissionId: "serve-3" })} />);
  fireEvent.click(await screen.findByRole("button", { name: /work in steps/i }));
  await screen.findByRole("region", { name: "workbench" });
  fireEvent.click(screen.getByRole("button", { name: "answer box instead" }));
  await screen.findByRole("textbox", { name: "answer" });
  expect(screen.queryByText(/Start from A\^T A\./)).toBeNull();
  await waitFor(() => expect(screen.getByTestId("help-record").textContent).toBe(
    "help used: an earlier attempt's help (counts as a hint)"));
  fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));
  const foot = await screen.findByTestId("ask-earlier");
  await waitFor(() => expect(foot.textContent).toContain("opened · counted as a hint"));
});
