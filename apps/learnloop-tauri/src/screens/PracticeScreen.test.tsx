import type { ComponentProps } from "react";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { PracticeScreen } from "./PracticeScreen";
import { selectWithDraftFlush } from "../app/vaultTransition";

const { api } = vi.hoisted(() => ({ api: {
  getPracticeItem: vi.fn(), getProbeContract: vi.fn(), recoverPracticeSubmission: vi.fn(),
  acknowledgePracticeSubmission: vi.fn(), savePracticeDraft: vi.fn(), submitAttempt: vi.fn(),
  getNextProbeItem: vi.fn()
} }));
vi.mock("../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn() }) }));
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
