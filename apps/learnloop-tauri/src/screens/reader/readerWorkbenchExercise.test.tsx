// RW4b's "use this one" in the working posture (spec §7.4, §5.1; UX §4.6):
// the shell's exercise opens once its own source is open, at once, on the
// verbatim statement, with the sources service's import (a proposal's
// exercise) or the Reader's (the fallback's) running behind it; the shell is
// told exactly once when that import binds the problem to the item it
// wrote (running → admitted), so the item becomes a learner pick; a refused
// import binds nothing and admits nothing.
import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import type { SourceLibraryCard, WorkbenchSessionDto } from "../../api/dto";
import { readerCheckOffer } from "../../app/readerCheck";
import { readerWorkbenchCheck } from "../../app/readerWorkbench";
import type { ReaderWorkbenchExercise } from "./exerciseCandidates";
import { useReaderWorkbench } from "./useReaderWorkbench";

const { api } = vi.hoisted(() => ({ api: { workbenchOpen: vi.fn(), workbenchForSource: vi.fn() } }));
vi.mock("../../api/client", () => ({ api }));

const book = { sourceId: "src_text", title: "Matrix Theory", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard;
const other = { ...book, sourceId: "src_other", title: "Other" } as SourceLibraryCard;

const EXERCISE: ReaderWorkbenchExercise = {
  key: "srcex:ext_text:t6", sourceId: "src_text", extractionId: "ext_text", spanIds: ["t6"],
  stemMd: "1. Solve 3x + 5 = 20 for x.", entry: "practice_this", proposalId: "pp_1",
  sourceExercise: { proposalId: "pp_1", extractionId: "ext_text", spanIds: ["t6"] },
};

function session(extra: Partial<WorkbenchSessionDto> = {}): WorkbenchSessionDto {
  return {
    sessionId: "wbs_1", practiceItemId: null, stemMd: EXERCISE.stemMd, importStatus: "pending", importError: null, origin: "reader",
    entry: "practice_this", parentSessionId: null, extractionId: "ext_text", spanIds: ["t6"], sourceVisible: false, sourceHiddenAt: null,
    sourceShownAt: null, practiceSessionId: null, helpStyle: null, status: "open", attemptId: null, createdAt: "t", updatedAt: "t",
    closedAt: null, steps: [], lastEditedStepId: null, record: {} as WorkbenchSessionDto["record"], parts: null, sourceId: "src_text",
    sourceExercise: { proposalId: "pp_1", importId: "sei_1", importStatus: "authoring", reason: null, keyStatus: null, keyLabel: "" },
    ...extra,
  };
}

beforeEach(() => {
  api.workbenchOpen.mockReset();
  api.workbenchForSource.mockReset();
  api.workbenchForSource.mockResolvedValue({ sessions: [] });
});

function hook(card: SourceLibraryCard, exercise: ReaderWorkbenchExercise | null) {
  const onExerciseShown = vi.fn();
  const onExerciseAdmitted = vi.fn();
  const onError = vi.fn();
  const rendered = renderHook(
    ({ card: open, exercise: wanted }) => useReaderWorkbench({
      enabled: true, extractionId: open.sourceId === "src_text" ? "ext_text" : "ext_other", card: open, onError,
      props: { exercise: wanted, onExerciseShown, onExerciseAdmitted },
    }),
    { initialProps: { card, exercise } },
  );
  return { ...rendered, onExerciseShown, onExerciseAdmitted, onError };
}

it("opens at once on the verbatim stem with the sources service's import, once its own source is open", async () => {
  api.workbenchOpen.mockResolvedValue({ version: 1, session: session(), resumed: false });
  const { result, rerender, onExerciseShown } = hook(other, EXERCISE);
  await act(async () => undefined);
  expect(api.workbenchOpen).not.toHaveBeenCalled(); // another book is open: it waits for its own
  rerender({ card: book, exercise: EXERCISE });
  await waitFor(() => expect(api.workbenchOpen).toHaveBeenCalledTimes(1));
  expect(api.workbenchOpen.mock.calls[0][0]).toMatchObject({
    origin: "reader", entry: "practice_this", stemMd: EXERCISE.stemMd, extractionId: "ext_text", spanIds: ["t6"],
    sourceExercise: { proposalId: "pp_1", extractionId: "ext_text", spanIds: ["t6"] },
  });
  expect(api.workbenchOpen.mock.calls[0][0].importRequest).toBeUndefined();
  await waitFor(() => expect(result.current.active?.session.sessionId).toBe("wbs_1"));
  expect(onExerciseShown).toHaveBeenCalledTimes(1);
});

const OWED = { proposalId: "pp_1", exposure: null, exposureChecked: "selection" as const, admitted: false, due: true };
function bound(extra: Partial<WorkbenchSessionDto> = {}): WorkbenchSessionDto {
  return session({ importStatus: "bound", practiceItemId: "pi_ex_1", exercisePick: OWED,
    sourceExercise: { proposalId: "pp_1", importId: "sei_1", importStatus: "written", reason: null, keyStatus: "model_answer", keyLabel: "Model's answer, not checked" },
    ...extra });
}
const ADMITTED = {
  practiceItemId: "pi_ex_1", proposalId: "pp_1", importId: "sei_1", sourceId: "src_text", card: book, spanId: "t6",
  stemMd: EXERCISE.stemMd, workbenchSessionId: "wbs_1",
};

it("tells the shell when the import has bound the problem and its pick is owed, one hand-off at a time", async () => {
  api.workbenchOpen.mockResolvedValue({ version: 1, session: session({ exercisePick: { ...OWED, due: false } }), resumed: false });
  const { result, onExerciseAdmitted } = hook(book, EXERCISE);
  onExerciseAdmitted.mockResolvedValue(true);
  await waitFor(() => expect(result.current.active).not.toBeNull());
  act(() => result.current.update(session({ importStatus: "pending", exercisePick: { ...OWED, due: false } })));
  await act(async () => undefined);
  expect(onExerciseAdmitted).not.toHaveBeenCalled(); // still running: nothing to pick yet
  act(() => result.current.update(bound()));
  act(() => result.current.update(bound()));
  await act(async () => undefined);
  expect(onExerciseAdmitted).toHaveBeenCalledTimes(1);
  expect(onExerciseAdmitted).toHaveBeenCalledWith(ADMITTED);
  // Acknowledged by the server: nothing is owed any more.
  act(() => result.current.update(bound({ exercisePick: { ...OWED, due: false, admitted: true } })));
  await act(async () => undefined);
  expect(onExerciseAdmitted).toHaveBeenCalledTimes(1);
});

// Codex review F2: what is owed comes from the problem itself, so a restart
// (a fresh Reader, nothing remembered) or a second "use this one" on the
// already-bound problem still hands the pick over.
it("after a restart, resuming a bound problem whose pick is owed hands it over", async () => {
  api.workbenchOpen.mockResolvedValue({ version: 1, session: bound(), resumed: true });
  const { result, onExerciseAdmitted } = hook(book, null);
  onExerciseAdmitted.mockResolvedValue(true);
  await act(async () => result.current.resume("wbs_1"));
  await waitFor(() => expect(onExerciseAdmitted).toHaveBeenCalledWith(ADMITTED));
});

it("use this one on a problem its import already bound hands the owed pick over", async () => {
  api.workbenchOpen.mockResolvedValue({ version: 1, session: bound(), resumed: true });
  const { onExerciseAdmitted } = hook(book, EXERCISE);
  onExerciseAdmitted.mockResolvedValue(true);
  await waitFor(() => expect(onExerciseAdmitted).toHaveBeenCalledWith(ADMITTED));
});

it("a failed hand-off is tried again, by this visit or the next", async () => {
  api.workbenchOpen.mockResolvedValue({ version: 1, session: bound(), resumed: true });
  const { result, onExerciseAdmitted, unmount } = hook(book, null);
  onExerciseAdmitted.mockResolvedValueOnce(false).mockRejectedValueOnce(new Error("pick refused")).mockResolvedValue(true);
  await act(async () => result.current.resume("wbs_1"));
  await waitFor(() => expect(onExerciseAdmitted).toHaveBeenCalledTimes(1));
  act(() => result.current.update(bound())); // still owed (nothing acknowledged): tried again
  await waitFor(() => expect(onExerciseAdmitted).toHaveBeenCalledTimes(2));
  unmount();
  const next = hook(book, null); // the next visit, after a restart
  next.onExerciseAdmitted.mockResolvedValue(true);
  await act(async () => next.result.current.resume("wbs_1"));
  await waitFor(() => expect(next.onExerciseAdmitted).toHaveBeenCalledTimes(1));
});

it("the pick's hand-off names the problem it admits, so the server acknowledges it then", async () => {
  api.workbenchOpen.mockResolvedValue({ version: 1, session: bound({ exercisePick: { ...OWED, due: false, admitted: true } }), resumed: true });
  const offer = readerCheckOffer({ enabled: false, step: null } as never, "pi_ex_1", "pp_1", "sei_1");
  const check = readerWorkbenchCheck({ practiceItemId: "pi_ex_1", spanId: "t6", card: book, entry: "practice_this", admitsSessionId: "wbs_1" }, offer, "served");
  expect(check.admitsSessionId).toBe("wbs_1");
  const onExerciseAdmitted = vi.fn();
  renderHook(() => useReaderWorkbench({ enabled: true, extractionId: "ext_text", card: book, onError: vi.fn(),
    props: { checkMe: check, onCheckMeShown: vi.fn(), onExerciseAdmitted } }));
  await waitFor(() => expect(api.workbenchOpen).toHaveBeenCalledTimes(1));
  expect(api.workbenchOpen.mock.calls[0][0]).toMatchObject({ entry: "practice_this", practiceItemId: "pi_ex_1", admittedSessionId: "wbs_1" });
  await act(async () => undefined);
  expect(onExerciseAdmitted).not.toHaveBeenCalled(); // acknowledged: nothing owed
});

it("a refused import binds nothing and admits nothing", async () => {
  api.workbenchOpen.mockResolvedValue({ version: 1, session: session(), resumed: false });
  const { result, onExerciseAdmitted } = hook(book, EXERCISE);
  await waitFor(() => expect(result.current.active).not.toBeNull());
  act(() => result.current.update(session({ importStatus: "failed", importError: "LearnLoop couldn't check this answer key yet",
    sourceExercise: { proposalId: "pp_1", importId: "sei_1", importStatus: "rejected", reason: "LearnLoop couldn't check this answer key yet", keyStatus: "model_answer", keyLabel: "" } })));
  expect(onExerciseAdmitted).not.toHaveBeenCalled();
  expect(result.current.active?.session.practiceItemId).toBeNull();
});

it("a fallback exercise opens with the Reader's own import request, and an exposed one with the book", async () => {
  api.workbenchOpen.mockResolvedValue({ version: 1, session: session({ sourceExercise: undefined }), resumed: false });
  const request = { extractionId: "ext_text", rawSelection: { nodes: [{ spanId: "t6", start: 0, end: 20 }] } };
  const pick = { learningObjectIds: ["lo_matrices"], shownEventIds: ["see_1"] };
  hook(book, { ...EXERCISE, proposalId: null, sourceExercise: undefined, importRequest: request, entry: "work_through", exercisePick: pick });
  await waitFor(() => expect(api.workbenchOpen).toHaveBeenCalledTimes(1));
  expect(api.workbenchOpen.mock.calls[0][0]).toMatchObject({ entry: "work_through", importRequest: request, exercisePick: pick });
  expect(api.workbenchOpen.mock.calls[0][0].sourceExercise).toBeUndefined();
});

it("the admitted pick carries its import, and resumes its own problem keeping the book choice", () => {
  const offer = readerCheckOffer({ enabled: false, step: null } as never, "pi_ex_1", "pp_1", "sei_1");
  expect(offer.proposalOrigin).toEqual({ proposalId: "pp_1", importId: "sei_1" });
  const check = readerWorkbenchCheck({ practiceItemId: "pi_ex_1", spanId: "t6", card: book, entry: "practice_this" }, offer, "served");
  expect(check.entry).toBe("practice_this");
  // A cue's check is unchanged: no entry, so the hook opens it as "check_me".
  expect(readerWorkbenchCheck({ practiceItemId: "pi_1", spanId: "t6", card: book }, offer, "served").entry).toBeUndefined();
  expect(readerCheckOffer({ enabled: false, step: null } as never, "pi_1", "pp_1").proposalOrigin).toEqual({ proposalId: "pp_1", importId: null });
});

// Codex re-review F2: the shell's hand-off resolves once the pick is made and
// served, before its acknowledging open runs. When that open fails, nothing
// was acknowledged, so the hand-off is released and the next sight of the
// problem (an update, a resume) hands the owed pick over again, and its open
// carries the new serve.
it("an acknowledging open that failed releases the hand-off, so the owed pick is handed over again", async () => {
  const onExerciseAdmitted = vi.fn().mockResolvedValue(true);
  const onError = vi.fn();
  const check = (serve: string) => ({
    practiceItemId: "pi_ex_1", spanId: "t6", sourceId: "src_text", stemMd: "served", entry: "practice_this" as const,
    schedulerCandidateId: serve, planPresentationId: null, admitsSessionId: "wbs_1",
  });
  const { result, rerender } = renderHook(
    ({ checkMe }) => useReaderWorkbench({ enabled: true, extractionId: "ext_text", card: book, onError,
      props: { checkMe, onCheckMeShown: vi.fn(), onExerciseAdmitted } }),
    { initialProps: { checkMe: null as ReturnType<typeof check> | null } },
  );
  api.workbenchOpen.mockResolvedValueOnce({ version: 1, session: bound(), resumed: true });
  await act(async () => result.current.resume("wbs_1"));
  await waitFor(() => expect(onExerciseAdmitted).toHaveBeenCalledTimes(1));
  // The shell made and served the pick; its acknowledging open fails.
  api.workbenchOpen.mockRejectedValueOnce(new Error("sidecar timeout"));
  rerender({ checkMe: check("sc_1") });
  await waitFor(() => expect(onError).toHaveBeenCalledTimes(1));
  expect(api.workbenchOpen.mock.calls[1][0]).toMatchObject({ admittedSessionId: "wbs_1", schedulerCandidateId: "sc_1" });
  // Still owed: the next sight of the problem hands it over again...
  act(() => result.current.update(bound()));
  await waitFor(() => expect(onExerciseAdmitted).toHaveBeenCalledTimes(2));
  // ...and that pick's open acknowledges it, carrying its own serve.
  api.workbenchOpen.mockResolvedValueOnce({ version: 1, session: bound({ exercisePick: { ...OWED, due: false, admitted: true }, schedulerCandidateId: "sc_2" }), resumed: true });
  rerender({ checkMe: check("sc_2") });
  await waitFor(() => expect(api.workbenchOpen).toHaveBeenCalledTimes(3));
  expect(api.workbenchOpen.mock.calls[2][0]).toMatchObject({ admittedSessionId: "wbs_1", schedulerCandidateId: "sc_2" });
  await waitFor(() => expect(result.current.active?.schedulerCandidateId).toBe("sc_2"));
  act(() => result.current.update(bound({ exercisePick: { ...OWED, due: false, admitted: true } })));
  await act(async () => undefined);
  expect(onExerciseAdmitted).toHaveBeenCalledTimes(2);
});

// Codex re-review F6: an import refresh that answers after the learner moved
// to another book must not admit the exercise against that book. The owed
// pick waits (still due on the problem) until its own source is open again.
it("a late import answer from another book admits nothing until the exercise's own book is open again", async () => {
  api.workbenchOpen.mockResolvedValue({ version: 1, session: session(), resumed: false });
  const { result, rerender, onExerciseAdmitted } = hook(book, EXERCISE);
  onExerciseAdmitted.mockResolvedValue(true);
  await waitFor(() => expect(result.current.active).not.toBeNull());
  rerender({ card: other, exercise: null }); // the learner opens book B
  await act(async () => undefined);
  act(() => result.current.update(bound())); // A's import refresh answers late
  await act(async () => undefined);
  expect(onExerciseAdmitted).not.toHaveBeenCalled();
  rerender({ card: book, exercise: null }); // back to A: resuming hands it over, with A's card
  api.workbenchOpen.mockResolvedValue({ version: 1, session: bound(), resumed: true });
  await act(async () => result.current.resume("wbs_1"));
  await waitFor(() => expect(onExerciseAdmitted).toHaveBeenCalledWith(ADMITTED));
});

it("a problem whose source is not the open card's admits nothing", async () => {
  // The card and the extraction can disagree for a moment while a book opens.
  const onExerciseAdmitted = vi.fn().mockResolvedValue(true);
  const { result } = renderHook(() => useReaderWorkbench({ enabled: true, extractionId: "ext_text", card: other, onError: vi.fn(),
    props: { onExerciseAdmitted } }));
  api.workbenchOpen.mockResolvedValue({ version: 1, session: bound(), resumed: true });
  await act(async () => result.current.resume("wbs_1"));
  await act(async () => undefined);
  expect(onExerciseAdmitted).not.toHaveBeenCalled();
});
