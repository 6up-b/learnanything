import type { ComponentProps } from "react";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { PracticeScreen } from "./PracticeScreen";
import { selectWithDraftFlush } from "../app/vaultTransition";

const { api } = vi.hoisted(() => ({ api: {
  getPracticeItem: vi.fn(), getProbeContract: vi.fn(), recoverPracticeSubmission: vi.fn(),
  acknowledgePracticeSubmission: vi.fn(), savePracticeDraft: vi.fn(), submitAttempt: vi.fn(),
  getNextProbeItem: vi.fn(), startTeachBack: vi.fn(), submitTeachBackTurn: vi.fn(),
  placementSelfReport: vi.fn()
} }));
vi.mock("../api/client", () => ({ api }));
const windowApi = vi.hoisted(() => ({
  closeHandler: null as null | ((event: { preventDefault: () => void }) => Promise<void>),
  destroy: vi.fn(),
}));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({
  onCloseRequested: async (handler: (event: { preventDefault: () => void }) => Promise<void>) => {
    windowApi.closeHandler = handler;
    return vi.fn();
  },
  destroy: windowApi.destroy,
}) }));
vi.mock("../render/MathLiveEditor", () => ({ MathLiveEditor: (props: { value: string; onChange: (value: string) => void; disabled: boolean }) => <textarea aria-label="answer" value={props.value} disabled={props.disabled} onChange={(event) => props.onChange(event.target.value)} /> }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: () => null }));
vi.mock("../components/ItemPresentation", () => ({ ItemPresentation: () => <p>Question</p> }));

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}
function props(): ComponentProps<typeof PracticeScreen> {
  return {
    session: { sessionId: "old-session" } as ComponentProps<typeof PracticeScreen>["session"],
    practiceItemId: "old-item", schedulerCandidateId: "old-offer", gradingReady: true, gradingProvider: "fake",
    onFeedback: vi.fn(), onBlockEnd: vi.fn(), onContinueDiagnostic: vi.fn(), onBack: vi.fn(),
    onCheckpointCleared: vi.fn(), onDraftSaved: vi.fn(), onTeachBackActive: vi.fn(),
    onAskAvailabilityChange: vi.fn(), onInspect: vi.fn(), onAsk: vi.fn(), onError: vi.fn()
  };
}
beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  api.getPracticeItem.mockResolvedValue({
    id: "old-item", learningObjectId: "lo", learningObjectTitle: "Topic", practiceMode: "open_text",
    attemptTypesAllowed: ["independent_attempt"], evidenceFacets: [], evidenceWeights: {}, hints: [],
    hintPolicy: { maxUsefulHints: 0 }, candidateErrorTypes: [], tags: [], sourceRefs: [], attempts: [], rubric: null
  });
  api.getProbeContract.mockResolvedValue({ version: 1, active: false });
  api.savePracticeDraft.mockResolvedValue({});
  api.acknowledgePracticeSubmission.mockResolvedValue({ acknowledged: true });
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

it("routes a saved deferred result before acknowledging its exact key, without resubmission", async () => {
  const next = deferred<{ active: boolean; practiceItemId: string }>();
  api.recoverPracticeSubmission.mockResolvedValue({ status: "recovered", result: { attemptId: "recorded", learningObjectId: "lo", probeEpisode: { feedbackDeferred: true } } });
  api.getNextProbeItem.mockReturnValue(next.promise);
  const callbacks = props();
  render(<PracticeScreen {...callbacks} restoredSubmissionId="saved-key" />);
  await waitFor(() => expect(api.getNextProbeItem).toHaveBeenCalledOnce());
  expect(api.acknowledgePracticeSubmission).not.toHaveBeenCalled();
  await act(async () => next.resolve({ active: true, practiceItemId: "next-probe" }));
  await waitFor(() => expect(callbacks.onContinueDiagnostic).toHaveBeenCalledWith("next-probe"));
  expect(api.acknowledgePracticeSubmission).toHaveBeenCalledWith({ sessionId: "old-session", practiceItemId: "old-item", submissionId: "saved-key" });
  expect(callbacks.onFeedback).not.toHaveBeenCalled();
  expect(api.submitAttempt).not.toHaveBeenCalled();
  expect(api.savePracticeDraft).not.toHaveBeenCalled();
});

it("ignores recovery that arrives after unmount and preserves the retry key", async () => {
  const recovery = deferred<object>();
  api.recoverPracticeSubmission.mockReturnValue(recovery.promise);
  const callbacks = props();
  const view = render(<PracticeScreen {...callbacks} restoredSubmissionId="saved-key" />);
  view.unmount();
  await act(async () => recovery.resolve({ status: "recovered", result: { attemptId: "recorded" } }));
  expect(callbacks.onFeedback).not.toHaveBeenCalled();
  expect(api.acknowledgePracticeSubmission).not.toHaveBeenCalled();
  expect(api.savePracticeDraft).not.toHaveBeenCalled();
});

it("finishes the old vault's draft before selection and suppresses its unmount write", async () => {
  const saved = deferred<object>();
  api.savePracticeDraft.mockReturnValue(saved.promise);
  const view = render(<PracticeScreen {...props()} />);
  await screen.findByRole("textbox", { name: "answer" });
  fireEvent.change(screen.getByRole("textbox", { name: "answer" }), { target: { value: "my latest answer" } });
  const select = vi.fn().mockResolvedValue(undefined);
  let switching!: Promise<void>;
  await act(async () => { switching = selectWithDraftFlush(select); });
  expect(select).not.toHaveBeenCalled();
  expect(api.savePracticeDraft).toHaveBeenCalledWith(expect.objectContaining({ sessionId: "old-session", practiceItemId: "old-item", answerMd: "my latest answer", schedulerCandidateId: "old-offer" }));
  await act(async () => { saved.resolve({}); await switching; });
  const writes = api.savePracticeDraft.mock.calls.length;
  view.unmount();
  await act(async () => {});
  expect(select).toHaveBeenCalledOnce();
  expect(api.savePracticeDraft).toHaveBeenCalledTimes(writes);
});

it("keeps the old vault and restores editing if the draft save fails", async () => {
  api.savePracticeDraft.mockRejectedValue(new Error("disk unavailable"));
  render(<PracticeScreen {...props()} />);
  await screen.findByRole("textbox", { name: "answer" });
  const select = vi.fn();
  await act(async () => { await expect(selectWithDraftFlush(select)).rejects.toThrow("disk unavailable"); });
  expect(select).not.toHaveBeenCalled();
  expect(screen.getByRole("textbox", { name: "answer" })).toBeTruthy();
});

it("reloads the item when a vault switch fails while a saved-submission recovery was pending", async () => {
  const recovery = deferred<object>();
  api.recoverPracticeSubmission.mockReturnValue(recovery.promise);
  render(<PracticeScreen {...props()} restoredSubmissionId="saved-key" />);
  const selectFails = async () => {
    await recovery.promise;
    throw new Error("bad vault");
  };
  let switching!: Promise<unknown>;
  await act(async () => { switching = selectWithDraftFlush(selectFails).catch((error: unknown) => error); });
  await act(async () => {
    recovery.resolve({ status: "pending", result: null });
    await switching;
  });
  await screen.findByRole("textbox", { name: "answer" });
  expect(api.recoverPracticeSubmission).toHaveBeenCalledTimes(2);
  expect(api.getPracticeItem).toHaveBeenCalledOnce();
});

it("mirrors the draft to App when it unmounts during a vault switch", async () => {
  const saved = deferred<object>();
  api.savePracticeDraft.mockReturnValue(saved.promise);
  const callbacks = props();
  const view = render(<PracticeScreen {...callbacks} />);
  await screen.findByRole("textbox", { name: "answer" });
  fireEvent.change(screen.getByRole("textbox", { name: "answer" }), { target: { value: "newest text" } });
  let switching!: Promise<unknown>;
  await act(async () => { switching = selectWithDraftFlush(vi.fn()).catch((error: unknown) => error); });
  view.unmount();
  expect(callbacks.onDraftSaved).toHaveBeenCalledWith(expect.objectContaining({ practiceItemId: "old-item", answerMd: "newest text" }));
  await act(async () => { saved.resolve({}); await switching; });
});

it("waits for the vault switch's pending draft save before closing the window", async () => {
  const saved = deferred<object>();
  api.savePracticeDraft.mockReturnValue(saved.promise);
  render(<PracticeScreen {...props()} />);
  await screen.findByRole("textbox", { name: "answer" });
  fireEvent.change(screen.getByRole("textbox", { name: "answer" }), { target: { value: "unsaved" } });
  let switching!: Promise<unknown>;
  await act(async () => { switching = selectWithDraftFlush(vi.fn()).catch((error: unknown) => error); });
  const closing = windowApi.closeHandler!({ preventDefault: vi.fn() });
  await act(async () => {});
  expect(windowApi.destroy).not.toHaveBeenCalled();
  await act(async () => {
    saved.resolve({});
    await Promise.all([switching, closing]);
  });
  expect(windowApi.destroy).toHaveBeenCalledOnce();
});

it("carries the queue offer into both teach-back conversation calls", async () => {
  api.getPracticeItem.mockResolvedValue({
    id: "old-item", learningObjectId: "lo", learningObjectTitle: "Topic", practiceMode: "teach_back",
    attemptTypesAllowed: ["teach_back"], evidenceFacets: [], evidenceWeights: {}, hints: [],
    hintPolicy: { maxUsefulHints: 0 }, candidateErrorTypes: [], tags: [], sourceRefs: [], attempts: [], rubric: null
  });
  api.startTeachBack.mockResolvedValue({
    version: 1, practiceItemId: "old-item", prompt: "Teach it", learningObjectTitle: "Topic", budget: 2,
    state: { version: 1, practiceItemId: "old-item", planned: [], turns: [], askedCount: 0 }
  });
  api.submitTeachBackTurn.mockResolvedValue({
    version: 1, done: false, questionMd: "Why?", criterionId: "c1", tier: "core", facetTargets: [],
    questionNumber: 1, remaining: 1, asked: 1, budget: 2,
    state: {
      version: 1, practiceItemId: "old-item", planned: [], askedCount: 1,
      turns: [{ role: "learner", contentMd: "My explanation", criterionId: null }, { role: "ai", contentMd: "Why?", criterionId: "c1" }]
    }
  });
  render(<PracticeScreen {...props()} />);
  await waitFor(() => expect(api.startTeachBack).toHaveBeenCalledWith({ sessionId: "old-session", practiceItemId: "old-item", schedulerCandidateId: "old-offer" }));
  fireEvent.change(await screen.findByRole("textbox", { name: "answer" }), { target: { value: "My explanation" } });
  fireEvent.click(screen.getByRole("button", { name: /Start teaching/ }));
  await waitFor(() => expect(api.submitTeachBackTurn).toHaveBeenCalledWith(expect.objectContaining({
    sessionId: "old-session", practiceItemId: "old-item", schedulerCandidateId: "old-offer", answerMd: "My explanation"
  })));
});

// Re-review F5: "help before any work" is logged explicitly from the draft,
// because the elapsed seconds the overlay also sends are fractional.
it("tells the tutor whether an answer was started when the learner asks", async () => {
  const callbacks = props();
  render(<PracticeScreen {...callbacks} />);
  const answer = await screen.findByRole("textbox", { name: "answer" });
  await waitFor(() => expect(api.getProbeContract).toHaveBeenCalled());
  await waitFor(() => {
    fireEvent.keyDown(window, { key: "?" });
    expect(callbacks.onAsk).toHaveBeenCalledOnce();
  });
  expect(callbacks.onAsk).toHaveBeenLastCalledWith(expect.objectContaining({
    context: "practice", practiceItemId: "old-item", sessionId: "old-session", attemptProgress: "no_draft"
  }));
  fireEvent.change(answer, { target: { value: "   " } });
  fireEvent.keyDown(window, { key: "?" });
  expect(callbacks.onAsk).toHaveBeenLastCalledWith(expect.objectContaining({ attemptProgress: "no_draft" }));
  fireEvent.change(answer, { target: { value: "A = U" } });
  fireEvent.keyDown(window, { key: "?" });
  expect(callbacks.onAsk).toHaveBeenLastCalledWith(expect.objectContaining({ attemptProgress: "draft_started" }));
  expect(callbacks.onAsk).toHaveBeenCalledTimes(3);
});

// Command-palette asks (App) read the same state the screen's own ask sends.
it("registers its ask state for the command palette and clears it on unmount", async () => {
  const onAskState = vi.fn();
  const view = render(<PracticeScreen {...props()} onAskState={onAskState} />);
  const answer = await screen.findByRole("textbox", { name: "answer" });
  const reader = onAskState.mock.calls[0][0] as () => { openedAtMs: number; attemptProgress: string };
  expect(reader()).toEqual(expect.objectContaining({ attemptProgress: "no_draft" }));
  expect(typeof reader().openedAtMs).toBe("number");
  fireEvent.change(answer, { target: { value: "A = U" } });
  expect(reader().attemptProgress).toBe("draft_started");
  view.unmount();
  expect(onAskState).toHaveBeenLastCalledWith(null);
});

// Learner field F2: "I know this" on a card is offered only while placement is
// on; it marks the card's LO assumed known (not tested) and moves on.
it("does not offer 'I know this' while placement is off", async () => {
  render(<PracticeScreen {...props()} />);
  await screen.findByRole("textbox", { name: "answer" });
  expect(screen.queryByText("✓ I know this")).toBeNull();
});

it("offers 'I know this' while placement is on, then leaves the card", async () => {
  api.placementSelfReport.mockResolvedValue({});
  api.getPracticeItem.mockResolvedValue({
    id: "old-item", learningObjectId: "lo", learningObjectTitle: "Topic", practiceMode: "open_text",
    attemptTypesAllowed: ["independent_attempt"], evidenceFacets: [], evidenceWeights: {}, hints: [],
    hintPolicy: { maxUsefulHints: 0 }, candidateErrorTypes: [], tags: [], sourceRefs: [], attempts: [], rubric: null,
    placementActive: true
  });
  const callbacks = props();
  render(<PracticeScreen {...callbacks} />);
  const action = await screen.findByText("✓ I know this");
  await act(async () => { fireEvent.click(action); });
  // The session travels with the report, which clears this card's durable
  // draft server-side in the same transaction (a restart cannot reopen it).
  expect(api.placementSelfReport).toHaveBeenCalledWith({
    report: "know_this", practiceItemId: "old-item", sessionId: "old-session"
  });
  expect(callbacks.onBack).toHaveBeenCalled();
  expect(callbacks.onCheckpointCleared).toHaveBeenCalled();
});
