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

it("hands the answer box's draft key to the steps, so the Reader resumes one attempt (Astra batch review)", async () => {
  render(<PracticeScreen {...props()} />);
  fireEvent.click(await screen.findByRole("button", { name: /work in steps/i }));
  await waitFor(() => expect(api.workbenchOpen).toHaveBeenCalled());
  const sent = api.workbenchOpen.mock.calls[0][0];
  expect(typeof sent.submissionId).toBe("string");
  expect(sent.submissionId.length).toBeGreaterThan(0);
  // The same key the answer box drafts under.
  await waitFor(() => expect(api.savePracticeDraft).toHaveBeenCalled());
  const drafted = api.savePracticeDraft.mock.calls.map((call: unknown[]) => (call[0] as { submissionId?: string }).submissionId);
  expect(drafted).toContain(sent.submissionId);
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
  api.workbenchOpen.mockResolvedValue({ resumed: true, session: wb({ sessionId: "wb_old", steps: [
    { stepId: "a", chainId: "a", ordinal: 1, kind: "step", bodyMd: "U Sigma", deleted: false, createdAt: "x", editedAt: "x", versions: [] },
  ] }) });
  const view = render(<PracticeScreen {...props()} />);
  fireEvent.click(await screen.findByRole("button", { name: "resume your steps" }));
  // One explicit resume on this surface (review F4): a Reader problem moves here.
  await waitFor(() => expect(api.workbenchOpen).toHaveBeenCalledWith(expect.objectContaining({
    origin: "practice", entry: "practice_screen", sessionId: "wb_old",
  })));
  expect(((await screen.findByRole("textbox", { name: "Step 1" })) as HTMLTextAreaElement).value).toBe("U Sigma");
  view.unmount();
  window.localStorage.clear();
  api.workbenchOpen.mockClear();
  api.workbenchForItem.mockResolvedValue({ sessions: [{ sessionId: "wb_old", status: "abandoned", stepCount: 3 }] });
  api.workbenchOpen.mockResolvedValue({ resumed: true, session: wb({ sessionId: "wb_old" }) });
  render(<PracticeScreen {...props()} />);
  fireEvent.click(await screen.findByRole("button", { name: "reopen your steps" }));
  await waitFor(() => expect(api.workbenchOpen).toHaveBeenCalledWith(expect.objectContaining({ sessionId: "wb_old" })));
  expect(api.workbenchGet).not.toHaveBeenCalled();
});

// Review F2: assistance survives switching between the answer box and steps.
it("hints shown on the answer box go into steps with the work, and come back with it", async () => {
  api.getPracticeItem.mockResolvedValue({
    id: "pi_1", learningObjectId: "lo", learningObjectTitle: "Topic", practiceMode: "open_text", prompt: PROMPT,
    attemptTypesAllowed: ["independent_attempt", "hinted_attempt"], evidenceFacets: [], evidenceWeights: {},
    hints: ["Start from A^T A.", "Its eigenvectors are V."], hintPolicy: { maxUsefulHints: 2 }, candidateErrorTypes: [],
    tags: [], sourceRefs: [], attempts: [], rubric: null,
  });
  const carried = wb({ carriedHints: 1, record: { ...wb().record, hints: 1, carriedHints: 1, ownAttempt: false,
    line: "1 hint (1 shown on the answer box) → practice with help ◌ (not yet checked on your own)" } });
  api.workbenchOpen.mockResolvedValue({ session: carried, resumed: false });
  render(<PracticeScreen {...props()} />);
  fireEvent.click(await screen.findByRole("button", { name: /^hint$/i }));
  expect(await screen.findByText(/Start from A\^T A\./)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: /work in steps/i }));
  await waitFor(() => expect(api.workbenchOpen).toHaveBeenCalledWith(expect.objectContaining({ carriedHints: 1 })));
  await screen.findByRole("region", { name: "workbench" });
  // The hint stays in view, and the record line counts it before Submit.
  expect(screen.getByText(/Start from A\^T A\./)).toBeTruthy();
  expect(screen.getByTestId("workbench-record").textContent).toContain("1 shown on the answer box");
  // Back to the answer box: the hint is still counted (and shown) there.
  fireEvent.click(screen.getByRole("button", { name: "answer box instead" }));
  await screen.findByRole("textbox", { name: "answer" });
  expect(screen.getByText(/Start from A\^T A\./)).toBeTruthy();
});

it("a resumed problem that carried hints brings them back to the answer box", async () => {
  api.getPracticeItem.mockResolvedValue({
    id: "pi_1", learningObjectId: "lo", learningObjectTitle: "Topic", practiceMode: "open_text", prompt: PROMPT,
    attemptTypesAllowed: ["independent_attempt", "hinted_attempt"], evidenceFacets: [], evidenceWeights: {},
    hints: ["Start from A^T A.", "Its eigenvectors are V."], hintPolicy: { maxUsefulHints: 2 }, candidateErrorTypes: [],
    tags: [], sourceRefs: [], attempts: [], rubric: null,
  });
  api.workbenchForItem.mockResolvedValue({ sessions: [{ sessionId: "wb_old", status: "open", stepCount: 1 }] });
  api.workbenchOpen.mockResolvedValue({ resumed: true, session: wb({ sessionId: "wb_old", carriedHints: 2 }) });
  render(<PracticeScreen {...props()} />);
  fireEvent.click(await screen.findByRole("button", { name: "resume your steps" }));
  await screen.findByRole("region", { name: "workbench" });
  fireEvent.click(screen.getByRole("button", { name: "answer box instead" }));
  await screen.findByRole("textbox", { name: "answer" });
  expect(screen.getByText(/Start from A\^T A\./)).toBeTruthy();
  expect(screen.getByText(/Its eigenvectors are V\./)).toBeTruthy();
  expect(screen.queryByRole("button", { name: /hint again/i })).toBeNull();
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

// Re-review F1: in steps the problem shows as the session froze it, the
// contract its submit is graded against, not the item as it is now.
it("in steps the problem shows the presentation the session froze, not the item's current one", async () => {
  api.getPracticeItem.mockResolvedValue({
    id: "pi_1", learningObjectId: "lo", learningObjectTitle: "Topic", practiceMode: "open_text", prompt: PROMPT,
    attemptTypesAllowed: ["independent_attempt"], evidenceFacets: [], evidenceWeights: {}, hints: [],
    hintPolicy: { maxUsefulHints: 0 }, candidateErrorTypes: [], tags: [], sourceRefs: [], attempts: [], rubric: null,
    presentation: { practiceItemId: "pi_1", blocks: [
      { kind: "prompt", markdown: PROMPT, label: null },
      { kind: "required_method_instruction", markdown: "Use the eigendecomposition of A^T A.", label: null },
    ] },
  });
  api.workbenchForItem.mockResolvedValue({ sessions: [{ sessionId: "wb_old", status: "open", stepCount: 1 }] });
  api.workbenchOpen.mockResolvedValue({ resumed: true, session: wb({ sessionId: "wb_old", presentation: { practiceItemId: "pi_1", blocks: [
    { kind: "prompt", markdown: PROMPT, label: null },
    { kind: "required_method_instruction", markdown: "Use Gram-Schmidt.", label: null },
  ] } }) });
  render(<PracticeScreen {...props()} />);
  expect((await screen.findByTestId("item-presentation")).textContent).toContain("eigendecomposition");
  fireEvent.click(await screen.findByRole("button", { name: "resume your steps" }));
  await screen.findByRole("region", { name: "workbench" });
  const shown = screen.getByTestId("item-presentation").textContent ?? "";
  expect(shown).toContain("Use Gram-Schmidt.");
  expect(shown).not.toContain("eigendecomposition");
});

// Re-review F2: a book the problem counted comes back to the answer box
// (and counts there), and goes back into steps with the learner.
it("a book counted in steps counts on the answer box and goes back into steps", async () => {
  api.getPracticeItem.mockResolvedValue({
    id: "pi_1", learningObjectId: "lo", learningObjectTitle: "Topic", practiceMode: "open_text", prompt: PROMPT,
    attemptTypesAllowed: ["independent_attempt", "hinted_attempt"], evidenceFacets: [], evidenceWeights: {}, hints: [],
    hintPolicy: { maxUsefulHints: 0 }, candidateErrorTypes: [], tags: [], sourceRefs: [], attempts: [], rubric: null,
  });
  api.workbenchForItem.mockResolvedValue({ sessions: [{ sessionId: "wb_old", status: "abandoned", stepCount: 1, bookCounted: true }] });
  const counted = wb({ sessionId: "wb_old", sourceShownAt: "x", record: { ...wb().record, bookCounted: true, hints: 1, ownAttempt: false,
    line: "book open · 1 hint → practice with help ◌ (not yet checked on your own)", footer: "book open = 1 hint · help used: none" } });
  api.workbenchOpen.mockResolvedValue({ resumed: true, session: counted });
  api.workbenchSubmit.mockResolvedValue({});
  api.submitAttempt.mockRejectedValue({ code: "grading_unavailable", message: "stop here" });
  render(<PracticeScreen {...props({ planPresentationId: "pres_1" })} />);
  fireEvent.click(await screen.findByRole("button", { name: "reopen your steps" }));
  await screen.findByRole("region", { name: "workbench" });
  fireEvent.click(screen.getByRole("button", { name: "answer box instead" }));
  const box = await screen.findByRole("textbox", { name: "answer" });
  expect(screen.getByTestId("book-carried").textContent).toContain("counts as one hint");
  // Into steps again (a new problem, say): the book goes with the learner.
  api.workbenchOpen.mockClear();
  fireEvent.click(screen.getByRole("button", { name: /work in steps/i }));
  await waitFor(() => expect(api.workbenchOpen).toHaveBeenCalledWith(expect.objectContaining({ carriedBook: true, carriedHints: 0 })));
  await screen.findByRole("region", { name: "workbench" });
  fireEvent.click(screen.getByRole("button", { name: "answer box instead" }));
  // Answered on the answer box, the attempt counts the book.
  fireEvent.change(await screen.findByRole("textbox", { name: "answer" }), { target: { value: "A = U Sigma V^T" } });
  fireEvent.keyDown(window, { key: "Enter", ctrlKey: true });
  await waitFor(() => expect(api.submitAttempt).toHaveBeenCalledWith(expect.objectContaining({ hintsUsed: 1, attemptType: "hinted_attempt" })));
  expect(box).toBeTruthy();
});

// Re-review F13: the practice screen's serve goes on the problem, so a
// resume elsewhere still submits as it.
it("opening steps puts this serve's offer and plan presentation on the problem", async () => {
  render(<PracticeScreen {...props({ planPresentationId: "pres_1" })} />);
  fireEvent.click(await screen.findByRole("button", { name: /work in steps/i }));
  await waitFor(() => expect(api.workbenchOpen).toHaveBeenCalledWith(expect.objectContaining({
    schedulerCandidateId: "cand_1", planPresentationId: "pres_1",
  })));
});

// Final verification F2: the answer box never submits a problem's
// assistance as the learner's own because its lookup had not answered yet.
it("final F2: Submit waits for the item's problems to be looked up, then counts the book one counted", async () => {
  api.getPracticeItem.mockResolvedValue({
    id: "pi_1", learningObjectId: "lo", learningObjectTitle: "Topic", practiceMode: "open_text", prompt: PROMPT,
    attemptTypesAllowed: ["independent_attempt", "hinted_attempt"], evidenceFacets: [], evidenceWeights: {}, hints: [],
    hintPolicy: { maxUsefulHints: 0 }, candidateErrorTypes: [], tags: [], sourceRefs: [], attempts: [], rubric: null,
  });
  let answer!: (value: unknown) => void;
  api.workbenchForItem.mockImplementation(() => new Promise((resolve) => { answer = resolve; }));
  api.submitAttempt.mockRejectedValue({ code: "grading_unavailable", message: "stop here" });
  render(<PracticeScreen {...props()} />);
  fireEvent.change(await screen.findByRole("textbox", { name: "answer" }), { target: { value: "A = U Sigma V^T" } });
  await waitFor(() => expect(api.workbenchForItem).toHaveBeenCalled());
  fireEvent.keyDown(window, { key: "Enter", ctrlKey: true });
  await new Promise((resolve) => setTimeout(resolve, 50));
  expect(api.submitAttempt).not.toHaveBeenCalled();
  answer({ sessions: [{ sessionId: "wb_r", status: "open", stepCount: 1, bookCounted: true }] });
  expect(await screen.findByTestId("book-carried")).toBeTruthy();
  fireEvent.keyDown(window, { key: "Enter", ctrlKey: true });
  await waitFor(() => expect(api.submitAttempt).toHaveBeenCalledWith(expect.objectContaining({ hintsUsed: 1, attemptType: "hinted_attempt" })));
});

it("final F2: a failed lookup is never read as no assistance: it says so, and a later failure keeps what was found", async () => {
  api.workbenchForItem.mockRejectedValueOnce({ code: "sidecar_unavailable", message: "down" });
  const first = render(<PracticeScreen {...props()} />);
  expect(await screen.findByTestId("assist-lookup-failed")).toBeTruthy();
  first.unmount();
  api.workbenchForItem.mockReset();
  api.workbenchForItem.mockResolvedValueOnce({ sessions: [{ sessionId: "wb_r", status: "open", stepCount: 1, bookCounted: true }] });
  api.workbenchForItem.mockRejectedValue({ code: "sidecar_unavailable", message: "down" });
  render(<PracticeScreen {...props()} />);
  expect(await screen.findByTestId("book-carried")).toBeTruthy();
  // Into steps and back: the refresh after leaving fails, and the book still counts.
  fireEvent.click(screen.getByRole("button", { name: /work in steps/i }));
  await screen.findByRole("region", { name: "workbench" });
  fireEvent.click(screen.getByRole("button", { name: /leave for now/ }));
  await screen.findByRole("textbox", { name: "answer" });
  await waitFor(() => expect(api.workbenchForItem).toHaveBeenCalledTimes(2));
  await new Promise((resolve) => setTimeout(resolve, 20));
  expect(screen.getByTestId("book-carried")).toBeTruthy();
});

it("final F2: hints a problem carried still count after the item's authored hints were removed", async () => {
  // The item shows no hints today; the problem carried two from before.
  api.getPracticeItem.mockResolvedValue({
    id: "pi_1", learningObjectId: "lo", learningObjectTitle: "Topic", practiceMode: "open_text", prompt: PROMPT,
    attemptTypesAllowed: ["independent_attempt", "hinted_attempt"], evidenceFacets: [], evidenceWeights: {}, hints: [],
    hintPolicy: { maxUsefulHints: 0 }, candidateErrorTypes: [], tags: [], sourceRefs: [], attempts: [], rubric: null,
  });
  api.workbenchForItem.mockResolvedValue({ sessions: [{ sessionId: "wb_old", status: "open", stepCount: 1 }] });
  api.workbenchOpen.mockResolvedValue({ resumed: true, session: wb({ sessionId: "wb_old", carriedHints: 2 }) });
  api.submitAttempt.mockRejectedValue({ code: "grading_unavailable", message: "stop here" });
  render(<PracticeScreen {...props()} />);
  fireEvent.click(await screen.findByRole("button", { name: "resume your steps" }));
  await screen.findByRole("region", { name: "workbench" });
  fireEvent.click(screen.getByRole("button", { name: "answer box instead" }));
  fireEvent.change(await screen.findByRole("textbox", { name: "answer" }), { target: { value: "A = U Sigma V^T" } });
  expect(screen.getByTestId("hints-carried").textContent).toContain("2 hints you saw earlier on this problem count");
  fireEvent.keyDown(window, { key: "Enter", ctrlKey: true });
  await waitFor(() => expect(api.submitAttempt).toHaveBeenCalledWith(expect.objectContaining({ hintsUsed: 2, attemptType: "hinted_attempt" })));
});
