// RW4b's "use this one" in the working posture (spec §7.4, §5.1; UX §4.6):
// the shell's exercise opens once its own source is open, at once, on the
// verbatim statement, with the sources service's import (a proposal's
// exercise) or the Reader's (the fallback's) running behind it; the shell is
// told exactly once when that import binds the problem to the item it
// wrote (running → admitted), so the item becomes a learner pick; a refused
// import binds nothing and admits nothing.
import { act, renderHook, waitFor } from "@testing-library/react";
import { useState } from "react";
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

// ── Fix round 3 (orchestrator rulings R1-R4) ─────────────────────────────────
// R1: what a problem is owed is kept per problem (session id -> its hand-off),
// never in one shared slot, so another problem's pick cannot displace it.
// R2: every answer is checked against the request it answers (the book, the
// extraction, the request token) before anything changes. R3: a submit goes
// back to the submitted problem's own book.

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

// Book B's owed exercise (a second problem, on the other book).
const ADMITTED_B = { practiceItemId: "pi_ex_2", workbenchSessionId: "wbs_2", sourceId: "src_other", spanId: "o3" };
function boundB(extra: Partial<WorkbenchSessionDto> = {}): WorkbenchSessionDto {
  return bound({ sessionId: "wbs_2", practiceItemId: "pi_ex_2", extractionId: "ext_other", sourceId: "src_other", spanIds: ["o3"],
    stemMd: "2. Invert the matrix.", ...extra });
}
const ACK = { ...OWED, due: false, admitted: true };
function checkFor(admitted: { practiceItemId: string; workbenchSessionId: string; sourceId: string; spanId: string }, serve: string) {
  return {
    practiceItemId: admitted.practiceItemId, spanId: admitted.spanId, sourceId: admitted.sourceId, stemMd: "served",
    entry: "practice_this" as const, schedulerCandidateId: serve, planPresentationId: null, admitsSessionId: admitted.workbenchSessionId,
  };
}
// The server: a resume answers the problem as it stands; an acknowledging open
// (admittedSessionId) acknowledges that problem's pick and resumes it.
function serverFor(sessions: Record<string, () => WorkbenchSessionDto>, gates: Record<string, Promise<void>> = {}) {
  api.workbenchOpen.mockImplementation(async (params: Record<string, unknown>) => {
    const id = (params.admittedSessionId ?? params.sessionId) as string;
    if (id in gates && !params.admittedSessionId) await gates[id];
    const session = sessions[id]();
    if (params.admittedSessionId) {
      return { version: 1, session: { ...session, exercisePick: ACK, schedulerCandidateId: params.schedulerCandidateId }, resumed: true };
    }
    return { version: 1, session, resumed: true };
  });
}
const acknowledging = (sessionId: string) => api.workbenchOpen.mock.calls.filter(([params]) => params.admittedSessionId === sessionId);
const extractionOf = (card: SourceLibraryCard) => (card.sourceId === "src_text" ? "ext_text" : "ext_other");

// Codex final verify F2, exactly as written, with the shell's single check
// slot as App.tsx keeps it (the pick resolves after setting the slot).
it("R1 (verify F2): a pending pick for A survives B's check replacing it in the shell's slot, and A gets it on return", async () => {
  serverFor({ wbs_1: () => bound(), wbs_2: () => boundB() });
  const picks: Record<string, ReturnType<typeof deferred<void>>> = { wbs_1: deferred<void>(), wbs_2: deferred<void>() };
  const setSlot: { current: (check: ReturnType<typeof checkFor> | null) => void } = { current: () => undefined };
  const onExerciseAdmitted = vi.fn(async (admitted: typeof ADMITTED_B) => {
    await picks[admitted.workbenchSessionId].promise; // the pick and its serve
    setSlot.current(checkFor(admitted, `sc_${admitted.workbenchSessionId}`));
    return true;
  });
  const { result, rerender } = renderHook(({ card }) => {
    const [slot, setSlotState] = useState<ReturnType<typeof checkFor> | null>(null);
    setSlot.current = setSlotState;
    return useReaderWorkbench({ enabled: true, extractionId: extractionOf(card), card, onError: vi.fn(),
      props: { checkMe: slot, onCheckMeShown: () => setSlotState(null), onExerciseAdmitted } });
  }, { initialProps: { card: book } });
  // 1. Resume A's bound exercise; its pick and serve are delayed.
  await act(async () => result.current.resume("wbs_1"));
  await waitFor(() => expect(onExerciseAdmitted).toHaveBeenCalledTimes(1));
  // 2. Switch to book B, then finish A's serve: its check waits in the slot.
  rerender({ card: other });
  await act(async () => { picks.wbs_1.resolve(); await picks.wbs_1.promise; });
  await act(async () => undefined);
  // 3. Resume B's owed exercise: its check replaces A's in the slot and opens.
  await act(async () => result.current.resume("wbs_2"));
  await act(async () => { picks.wbs_2.resolve(); await picks.wbs_2.promise; });
  await waitFor(() => expect(acknowledging("wbs_2")).toHaveLength(1));
  // 4. Return to A and resume its still-due problem: A's pick is handed over.
  rerender({ card: book });
  await act(async () => result.current.resume("wbs_1"));
  await waitFor(() => expect(acknowledging("wbs_1")).toHaveLength(1));
  expect(acknowledging("wbs_1")[0][0]).toMatchObject({ schedulerCandidateId: "sc_wbs_1", extractionId: "ext_text" });
  await waitFor(() => expect(result.current.active?.session.exercisePick?.admitted).toBe(true));
  expect(result.current.active?.session.sessionId).toBe("wbs_1");
});

// The shell's hand-off resolves the served pick itself (App.tsx after R1):
// A, B, A. A's pick is made once and delivered exactly once, on A's return.
it("R1: A/B/A interleaving delivers A's owed pick exactly once after returning to A", async () => {
  serverFor({ wbs_1: () => bound(), wbs_2: () => boundB() });
  const pickA = deferred<ReturnType<typeof checkFor>>();
  const onExerciseAdmitted = vi.fn((admitted: typeof ADMITTED_B) => (admitted.workbenchSessionId === "wbs_1"
    ? pickA.promise : Promise.resolve(checkFor(admitted, "sc_b"))));
  const { result, rerender } = renderHook(({ card }) => useReaderWorkbench({ enabled: true, extractionId: extractionOf(card), card,
    onError: vi.fn(), props: { onExerciseAdmitted } }), { initialProps: { card: book } });
  await act(async () => result.current.resume("wbs_1")); // A
  await waitFor(() => expect(onExerciseAdmitted).toHaveBeenCalledTimes(1));
  rerender({ card: other }); // B
  await act(async () => { pickA.resolve(checkFor({ ...ADMITTED, sourceId: "src_text" }, "sc_a")); await pickA.promise; });
  expect(acknowledging("wbs_1")).toHaveLength(0); // not on A's book: it waits, owed
  await act(async () => result.current.resume("wbs_2"));
  await waitFor(() => expect(acknowledging("wbs_2")).toHaveLength(1));
  expect(acknowledging("wbs_1")).toHaveLength(0);
  rerender({ card: book }); // A again
  await act(async () => result.current.resume("wbs_1"));
  await waitFor(() => expect(acknowledging("wbs_1")).toHaveLength(1));
  expect(acknowledging("wbs_1")[0][0]).toMatchObject({ schedulerCandidateId: "sc_a" });
  await waitFor(() => expect(result.current.active?.session.sessionId).toBe("wbs_1"));
  // More sights of A change nothing: one pick, one delivery.
  act(() => result.current.update(bound({ exercisePick: ACK })));
  await act(async () => result.current.resume("wbs_1"));
  await act(async () => undefined);
  expect(onExerciseAdmitted.mock.calls.filter(([admitted]) => admitted.workbenchSessionId === "wbs_1")).toHaveLength(1);
  expect(acknowledging("wbs_1")).toHaveLength(1);
});

// Codex final verify F6, exactly as written.
it("R2 (verify F6): a late resume for A's exercise, answering after book B opened, activates nothing", async () => {
  const gate = deferred<void>();
  serverFor({ wbs_1: () => bound() }, { wbs_1: gate.promise });
  const onSubmitted = vi.fn();
  const { result, rerender } = renderHook(({ card }) => useReaderWorkbench({ enabled: true, extractionId: extractionOf(card), card,
    onError: vi.fn(), props: { onSubmitted, onExerciseAdmitted: vi.fn().mockResolvedValue(true) } }), { initialProps: { card: book } });
  // 1. Start resuming A's exercise, its open delayed. 2. Switch to B.
  let resumed!: Promise<void>;
  act(() => { resumed = result.current.resume("wbs_1"); });
  rerender({ card: other });
  // 3. A's resume answers.
  await act(async () => { gate.resolve(); await resumed; });
  expect(result.current.active).toBeNull(); // B is displayed: A's problem is not active
  // 4. A submit of A's problem landing now changes nothing either.
  act(() => result.current.submitted({ attempt: { attemptId: "att_1" }, session: { ...bound(), status: "submitted" }, practiceSession: null } as never));
  expect(onSubmitted).not.toHaveBeenCalled();
});

it("R2: a stale open is dropped; the newer request's problem stays", async () => {
  const gate = deferred<void>();
  serverFor({ wbs_1: () => bound(), wbs_3: () => session({ sessionId: "wbs_3", stemMd: "3. Another." }) }, { wbs_1: gate.promise });
  const { result } = renderHook(() => useReaderWorkbench({ enabled: true, extractionId: "ext_text", card: book, onError: vi.fn(),
    props: { onExerciseAdmitted: vi.fn().mockResolvedValue(true) } }));
  let first!: Promise<void>;
  act(() => { first = result.current.resume("wbs_1"); });
  await act(async () => result.current.resume("wbs_3")); // the learner moved on
  expect(result.current.active?.session.sessionId).toBe("wbs_3");
  await act(async () => { gate.resolve(); await first; }); // the first answer arrives late
  expect(result.current.active?.session.sessionId).toBe("wbs_3");
});

it("R2: a stale post-attempt answer is dropped; it neither closes the problem now open nor leaves for feedback", async () => {
  serverFor({ wbs_1: () => bound(), wbs_3: () => session({ sessionId: "wbs_3", stemMd: "3. Another." }) });
  const onSubmitted = vi.fn();
  const { result } = renderHook(() => useReaderWorkbench({ enabled: true, extractionId: "ext_text", card: book, onError: vi.fn(),
    props: { onSubmitted } }));
  await act(async () => result.current.resume("wbs_1"));
  await act(async () => result.current.resume("wbs_3")); // A's submit is still in flight
  act(() => result.current.submitted({ attempt: { attemptId: "att_1" }, session: { ...bound(), status: "submitted" }, practiceSession: null } as never));
  expect(result.current.active?.session.sessionId).toBe("wbs_3");
  expect(onSubmitted).not.toHaveBeenCalled();
});

it("R3: a submit returns to the submitted problem's own book and passage, not the card shown at submit time", async () => {
  serverFor({ wbs_1: () => bound() });
  const onSubmitted = vi.fn();
  const { result, rerender } = renderHook(({ card }) => useReaderWorkbench({ enabled: true, extractionId: "ext_text", card, onError: vi.fn(),
    props: { onSubmitted } }), { initialProps: { card: book } });
  await act(async () => result.current.resume("wbs_1"));
  expect(result.current.active?.session.sessionId).toBe("wbs_1");
  // The open card moves to another book a moment before its extraction does.
  rerender({ card: other });
  const submittedResult = { attempt: { attemptId: "att_1" }, session: { ...bound(), status: "submitted" }, practiceSession: null } as never;
  act(() => result.current.submitted(submittedResult));
  expect(onSubmitted).toHaveBeenCalledWith(submittedResult, { card: book, spanId: "t6" });
});
