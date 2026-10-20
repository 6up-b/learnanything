// RW4b's "use this one" in the working posture (spec §7.4, §5.1; UX §4.6):
// the shell's exercise opens once its own source is open, at once, on the
// verbatim statement, with the sources service's import (a proposal's
// exercise) or the Reader's (the fallback's) running behind it. Once that
// import binds the problem to the item it wrote, the learner pick of it is
// owed on the server (`exercisePick.due`), and the hook asks the server's one
// admission (`workbench.admit`, fix round 4, R1) for THAT problem by its id;
// a refused import binds nothing and admits nothing.
//
// Fix rounds 3 and 4: every answer (open, resume, refresh, admit, submit) is
// checked against what it was asked for (its generation, the open book, its
// place among opens) before anything changes; a submit returns to its own book.
import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import type { SourceLibraryCard, WorkbenchSessionDto } from "../../api/dto";
import { readerCheckOffer } from "../../app/readerCheck";
import { readerWorkbenchCheck } from "../../app/readerWorkbench";
import type { ReaderWorkbenchExercise } from "./exerciseCandidates";
import { useReaderWorkbench } from "./useReaderWorkbench";

const { api } = vi.hoisted(() => ({ api: { workbenchOpen: vi.fn(), workbenchForSource: vi.fn(), workbenchAdmit: vi.fn() } }));
vi.mock("../../api/client", () => ({ api }));

const book = { sourceId: "src_text", title: "Matrix Theory", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard;
const other = { ...book, sourceId: "src_other", title: "Other" } as SourceLibraryCard;
const extractionOf = (card: SourceLibraryCard) => (card.sourceId === "src_text" ? "ext_text" : "ext_other");

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

const OWED = { proposalId: "pp_1", exposure: null, exposureChecked: "selection" as const, admitted: false, due: true };
const ACK = { ...OWED, due: false, admitted: true, exposureChecked: "admission" as const };
function bound(extra: Partial<WorkbenchSessionDto> = {}): WorkbenchSessionDto {
  return session({ importStatus: "bound", practiceItemId: "pi_ex_1", exercisePick: OWED,
    sourceExercise: { proposalId: "pp_1", importId: "sei_1", importStatus: "written", reason: null, keyStatus: "model_answer", keyLabel: "Model's answer, not checked" },
    ...extra });
}
function boundB(extra: Partial<WorkbenchSessionDto> = {}): WorkbenchSessionDto {
  return bound({ sessionId: "wbs_2", practiceItemId: "pi_ex_2", extractionId: "ext_other", sourceId: "src_other", spanIds: ["o3"],
    stemMd: "2. Invert the matrix.", ...extra });
}
const PS = { sessionId: "ps_1" } as never;
/** The server's admission: the problem asked about, admitted, with its serve. */
function admitted(of: WorkbenchSessionDto) {
  return { version: 1, session: { ...of, exercisePick: ACK, schedulerCandidateId: `cand_${of.sessionId}` }, practiceSession: PS };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

beforeEach(() => {
  api.workbenchOpen.mockReset();
  api.workbenchForSource.mockReset();
  api.workbenchAdmit.mockReset();
  api.workbenchForSource.mockResolvedValue({ sessions: [] });
});

function hook(card: SourceLibraryCard, exercise: ReaderWorkbenchExercise | null, extra: Record<string, unknown> = {}) {
  const onExerciseShown = vi.fn();
  const onPracticeSession = vi.fn();
  const onSubmitted = vi.fn();
  const onError = vi.fn();
  const rendered = renderHook(
    ({ card: open, exercise: wanted }) => useReaderWorkbench({
      enabled: true, extractionId: extractionOf(open), card: open, onError,
      props: { exercise: wanted, onExerciseShown, onPracticeSession, onSubmitted, practiceSessionId: "ps_app", ...extra },
    }),
    { initialProps: { card, exercise } },
  );
  return { ...rendered, onExerciseShown, onPracticeSession, onSubmitted, onError };
}
const admitsAsked = () => api.workbenchAdmit.mock.calls.map(([input]) => input.sessionId);

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
  expect(onExerciseShown).toHaveBeenCalledWith(EXERCISE); // the request it showed, by identity
});

it("once the import bound the problem, the server admits its owed pick, asked once while in flight", async () => {
  api.workbenchOpen.mockResolvedValue({ version: 1, session: session({ exercisePick: { ...OWED, due: false } }), resumed: false });
  const answer = deferred<ReturnType<typeof admitted>>();
  api.workbenchAdmit.mockReturnValue(answer.promise);
  const { result, onPracticeSession } = hook(book, EXERCISE);
  await waitFor(() => expect(result.current.active).not.toBeNull());
  act(() => result.current.update(session({ importStatus: "pending", exercisePick: { ...OWED, due: false } })));
  expect(api.workbenchAdmit).not.toHaveBeenCalled(); // still running: nothing to pick yet
  act(() => result.current.update(bound()));
  act(() => result.current.update(bound()));
  expect(admitsAsked()).toEqual(["wbs_1"]);
  expect(api.workbenchAdmit.mock.calls[0][0]).toEqual({ sessionId: "wbs_1", practiceSessionId: "ps_app" });
  await act(async () => { answer.resolve(admitted(bound())); await answer.promise; });
  // What the server answered is shown (its exposure, its serve), and the shell hears of the session.
  expect(result.current.active?.session.exercisePick).toEqual(ACK);
  expect(result.current.active?.session.schedulerCandidateId).toBe("cand_wbs_1");
  expect(onPracticeSession).toHaveBeenCalledWith(PS);
  act(() => result.current.update(bound({ exercisePick: ACK })));
  expect(admitsAsked()).toEqual(["wbs_1"]); // admitted: nothing owed
});

it("after a restart, resuming a bound problem whose pick is owed asks the server to admit it", async () => {
  api.workbenchOpen.mockResolvedValue({ version: 1, session: bound(), resumed: true });
  api.workbenchAdmit.mockResolvedValue(admitted(bound()));
  const { result } = hook(book, null);
  await act(async () => result.current.resume("wbs_1"));
  expect(api.workbenchOpen.mock.calls[0][0]).toMatchObject({ entry: "resume", sessionId: "wbs_1", extractionId: "ext_text" });
  await waitFor(() => expect(admitsAsked()).toEqual(["wbs_1"]));
});

it("use this one on a problem its import already bound asks the server to admit it", async () => {
  api.workbenchOpen.mockResolvedValue({ version: 1, session: bound(), resumed: true });
  api.workbenchAdmit.mockResolvedValue(admitted(bound()));
  hook(book, EXERCISE);
  await waitFor(() => expect(admitsAsked()).toEqual(["wbs_1"]));
});

it("a failed admission stays owed on the server and is asked again on the problem's next sight, never at once", async () => {
  api.workbenchOpen.mockResolvedValue({ version: 1, session: bound(), resumed: true });
  api.workbenchAdmit.mockRejectedValueOnce(new Error("admission_pending")).mockResolvedValue(admitted(bound()));
  const { result, onError, unmount } = hook(book, null);
  await act(async () => result.current.resume("wbs_1"));
  await waitFor(() => expect(onError).toHaveBeenCalledTimes(1));
  expect(admitsAsked()).toEqual(["wbs_1"]); // no retry loop
  act(() => result.current.update(bound())); // the next sight
  await waitFor(() => expect(admitsAsked()).toEqual(["wbs_1", "wbs_1"]));
  unmount();
  const next = hook(book, null); // the next visit, after a restart
  await act(async () => next.result.current.resume("wbs_1"));
  await waitFor(() => expect(admitsAsked()).toEqual(["wbs_1", "wbs_1", "wbs_1"]));
});

it("an admission answer for another problem than the one asked about is not shown", async () => {
  api.workbenchOpen.mockResolvedValue({ version: 1, session: bound(), resumed: true });
  api.workbenchAdmit.mockResolvedValue(admitted(bound({ sessionId: "wbs_9" })));
  const { result, onPracticeSession } = hook(book, null);
  await act(async () => result.current.resume("wbs_1"));
  await act(async () => undefined);
  expect(result.current.active?.session.exercisePick).toEqual(OWED);
  expect(onPracticeSession).not.toHaveBeenCalled();
});

it("a refused import binds nothing and admits nothing", async () => {
  api.workbenchOpen.mockResolvedValue({ version: 1, session: session(), resumed: false });
  const { result } = hook(book, EXERCISE);
  await waitFor(() => expect(result.current.active).not.toBeNull());
  act(() => result.current.update(session({ importStatus: "failed", importError: "LearnLoop couldn't check this answer key yet",
    sourceExercise: { proposalId: "pp_1", importId: "sei_1", importStatus: "rejected", reason: "LearnLoop couldn't check this answer key yet", keyStatus: "model_answer", keyLabel: "" } })));
  expect(api.workbenchAdmit).not.toHaveBeenCalled();
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

it("a library pick carries its import, and a check's entry keeps or hides the book", () => {
  const offer = readerCheckOffer({ enabled: false, step: null } as never, "pi_ex_1", "pp_1", "sei_1");
  expect(offer.proposalOrigin).toEqual({ proposalId: "pp_1", importId: "sei_1" });
  const check = readerWorkbenchCheck({ practiceItemId: "pi_ex_1", spanId: "t6", card: book, entry: "practice_this" }, offer, "served");
  expect(check.entry).toBe("practice_this");
  expect("admitsSessionId" in check).toBe(false); // no client-side acknowledgement any more (round 4, R1)
  expect(readerWorkbenchCheck({ practiceItemId: "pi_1", spanId: "t6", card: book }, offer, "served").entry).toBeUndefined();
  expect(readerCheckOffer({ enabled: false, step: null } as never, "pi_1", "pp_1").proposalOrigin).toEqual({ proposalId: "pp_1", importId: null });
});

// Codex re-review F6: an import refresh that answers after the learner moved
// to another book admits nothing; the pick stays owed until its own book is
// open again and the problem is seen there.
it("a late import answer from another book admits nothing until the exercise's own book is open again", async () => {
  api.workbenchOpen.mockResolvedValue({ version: 1, session: session(), resumed: false });
  api.workbenchAdmit.mockResolvedValue(admitted(bound()));
  const { result, rerender } = hook(book, EXERCISE);
  await waitFor(() => expect(result.current.active).not.toBeNull());
  rerender({ card: other, exercise: null }); // the learner opens book B
  act(() => result.current.update(bound())); // A's import refresh answers late
  await act(async () => undefined);
  expect(api.workbenchAdmit).not.toHaveBeenCalled();
  rerender({ card: book, exercise: null }); // back to A: resuming asks for it
  api.workbenchOpen.mockResolvedValue({ version: 1, session: bound(), resumed: true });
  await act(async () => result.current.resume("wbs_1"));
  await waitFor(() => expect(admitsAsked()).toEqual(["wbs_1"]));
});

it("a problem whose source is not the open card's is neither shown nor admitted", async () => {
  // The card and the extraction can disagree for a moment while a book opens.
  const { result } = renderHook(() => useReaderWorkbench({ enabled: true, extractionId: "ext_text", card: other, onError: vi.fn(),
    props: {} }));
  api.workbenchOpen.mockResolvedValue({ version: 1, session: bound(), resumed: true });
  await act(async () => result.current.resume("wbs_1"));
  await act(async () => undefined);
  expect(result.current.active).toBeNull();
  expect(api.workbenchAdmit).not.toHaveBeenCalled();
});

// A, B, A: A's admission is in flight when the learner opens book B; its
// answer is dropped there (stale), B's own admission is B's; back on A, A is
// asked again (the server's admission is idempotent) and A's answer is A's.
it("A/B/A: each problem's admission is its own; a stale answer is dropped and A is admitted on return", async () => {
  const sessions: Record<string, () => WorkbenchSessionDto> = { wbs_1: () => bound(), wbs_2: () => boundB() };
  api.workbenchOpen.mockImplementation(async (params: { sessionId: string }) => ({ version: 1, session: sessions[params.sessionId](), resumed: true }));
  const firstA = deferred<ReturnType<typeof admitted>>();
  api.workbenchAdmit.mockImplementation((input: { sessionId: string }) => (
    input.sessionId === "wbs_1" && api.workbenchAdmit.mock.calls.length === 1 ? firstA.promise : Promise.resolve(admitted(sessions[input.sessionId]()))));
  const { result, rerender } = hook(book, null);
  await act(async () => result.current.resume("wbs_1")); // A
  expect(admitsAsked()).toEqual(["wbs_1"]);
  rerender({ card: other, exercise: null }); // B's book
  await act(async () => { firstA.resolve(admitted(bound())); await firstA.promise; });
  expect(result.current.active).toBeNull(); // A's answer, stale, shows nothing on B's book
  await act(async () => result.current.resume("wbs_2"));
  await waitFor(() => expect(result.current.active?.session.exercisePick).toEqual(ACK));
  expect(result.current.active?.session.sessionId).toBe("wbs_2");
  rerender({ card: book, exercise: null }); // A again
  await act(async () => result.current.resume("wbs_1"));
  await waitFor(() => expect(result.current.active?.session.exercisePick).toEqual(ACK));
  expect(result.current.active?.session.sessionId).toBe("wbs_1");
  expect(result.current.active?.session.schedulerCandidateId).toBe("cand_wbs_1");
  expect(admitsAsked()).toEqual(["wbs_1", "wbs_2", "wbs_1"]);
});

// Codex final verify (round 3) F6, as written: a late resume for A's exercise.
it("R2 (verify F6): a late resume for A's exercise, answering after book B opened, activates nothing", async () => {
  const gate = deferred<void>();
  api.workbenchOpen.mockImplementation(async () => { await gate.promise; return { version: 1, session: bound(), resumed: true }; });
  const { result, rerender, onSubmitted } = hook(book, null);
  let resumed!: Promise<void>;
  act(() => { resumed = result.current.resume("wbs_1"); });
  rerender({ card: other, exercise: null });
  await act(async () => { gate.resolve(); await resumed; });
  expect(result.current.active).toBeNull();
  act(() => result.current.submitted({ attempt: { attemptId: "att_1" }, session: { ...bound(), status: "submitted" }, practiceSession: null } as never));
  expect(onSubmitted).not.toHaveBeenCalled();
  expect(api.workbenchAdmit).not.toHaveBeenCalled();
});

it("R2: a stale open is dropped; the newer request's problem stays", async () => {
  const gate = deferred<void>();
  api.workbenchOpen.mockImplementation(async (params: { sessionId: string }) => {
    if (params.sessionId === "wbs_1") await gate.promise;
    return { version: 1, session: params.sessionId === "wbs_1" ? bound() : session({ sessionId: "wbs_3", stemMd: "3. Another." }), resumed: true };
  });
  const { result } = hook(book, null);
  let first!: Promise<void>;
  act(() => { first = result.current.resume("wbs_1"); });
  await act(async () => result.current.resume("wbs_3"));
  expect(result.current.active?.session.sessionId).toBe("wbs_3");
  await act(async () => { gate.resolve(); await first; });
  expect(result.current.active?.session.sessionId).toBe("wbs_3");
});

it("R2: a stale post-attempt answer is dropped; it neither closes the problem now open nor leaves for feedback", async () => {
  api.workbenchOpen.mockImplementation(async (params: { sessionId: string }) => ({ version: 1,
    session: params.sessionId === "wbs_1" ? session() : session({ sessionId: "wbs_3", stemMd: "3. Another." }), resumed: true }));
  const { result, onSubmitted } = hook(book, null);
  await act(async () => result.current.resume("wbs_1"));
  const shownIn = result.current.active!.generation;
  await act(async () => result.current.resume("wbs_3")); // A's submit is still in flight
  act(() => result.current.submitted({ attempt: { attemptId: "att_1" }, session: { ...session(), status: "submitted" }, practiceSession: null } as never, shownIn));
  expect(result.current.active?.session.sessionId).toBe("wbs_3");
  expect(onSubmitted).not.toHaveBeenCalled();
});

it("R3: a submit returns to the submitted problem's own book and passage, not the card shown at submit time", async () => {
  api.workbenchOpen.mockResolvedValue({ version: 1, session: session(), resumed: true });
  const onSubmitted = vi.fn();
  const { result, rerender } = renderHook(({ card }) => useReaderWorkbench({ enabled: true, extractionId: "ext_text", card, onError: vi.fn(),
    props: { onSubmitted } }), { initialProps: { card: book } });
  await act(async () => result.current.resume("wbs_1"));
  expect(result.current.active?.session.sessionId).toBe("wbs_1");
  const shownIn = result.current.active!.generation;
  rerender({ card: other }); // the open card moves a moment before its extraction does
  const submittedResult = { attempt: { attemptId: "att_1" }, session: { ...session(), status: "submitted" }, practiceSession: null } as never;
  act(() => result.current.submitted(submittedResult, shownIn));
  expect(onSubmitted).toHaveBeenCalledWith(submittedResult, { card: book, spanId: "t6" });
});

// Codex final verify (round 4) F8, as written: an import refresh is in flight
// when the learner presses Leave; its answer (bound, owed) arrives after.
it("R5 (verify F8): a late import refresh after Leave neither reopens the problem nor admits it", async () => {
  api.workbenchOpen.mockResolvedValue({ version: 1, session: session(), resumed: true });
  api.workbenchAdmit.mockResolvedValue(admitted(bound()));
  // The round-3 shell's hand-off, so the same reproduction runs against it.
  const handOff = vi.fn().mockResolvedValue({ practiceItemId: "pi_ex_1", spanId: "t6", sourceId: "src_text", stemMd: "served",
    entry: "practice_this", schedulerCandidateId: "cand_1", planPresentationId: null, admitsSessionId: "wbs_1" });
  const { result } = hook(book, null, { onExerciseAdmitted: handOff });
  await act(async () => result.current.resume("wbs_1"));
  const shownIn = result.current.active!.generation;
  const opensBefore = api.workbenchOpen.mock.calls.length;
  act(() => { result.current.close(null); }); // Leave
  expect(result.current.active).toBeNull();
  await act(async () => { result.current.update(bound(), shownIn); }); // the refresh answers late
  await act(async () => undefined);
  expect(result.current.active).toBeNull();
  expect(api.workbenchAdmit).not.toHaveBeenCalled();
  expect(handOff).not.toHaveBeenCalled();
  expect(api.workbenchOpen.mock.calls.length).toBe(opensBefore);
});

it("R5: unmounting makes every answer still in flight stale", async () => {
  const gate = deferred<void>();
  api.workbenchOpen.mockImplementation(async () => { await gate.promise; return { version: 1, session: bound(), resumed: true }; });
  const { result, unmount, onError } = hook(book, null);
  let resumed!: Promise<void>;
  act(() => { resumed = result.current.resume("wbs_1"); });
  unmount();
  await act(async () => { gate.resolve(); await resumed; });
  expect(api.workbenchAdmit).not.toHaveBeenCalled();
  expect(onError).not.toHaveBeenCalled();
});

// Fix round 5, R5 (Codex final verify F12, as written): Leave on A is under
// way (its flush and RPC pending) when the learner opens B; A's departure
// then completes. It closes nothing, sets no receipt and jumps nowhere.
it("R5 (verify F12): a delayed Leave or Abandon of A never closes B", async () => {
  api.workbenchOpen.mockImplementation(async (params: { sessionId: string }) => ({ version: 1,
    session: params.sessionId === "wbs_1" ? session() : session({ sessionId: "wbs_3", stemMd: "3. Another." }), resumed: true }));
  const { result } = hook(book, null);
  await act(async () => result.current.resume("wbs_1"));
  const a = result.current.active!;
  await act(async () => result.current.resume("wbs_3")); // B opens while A's Leave is pending
  expect(result.current.active?.session.sessionId).toBe("wbs_3");
  let jump: string | null = "unset";
  act(() => { jump = result.current.close(a.session, { generation: a.generation }); }); // A's Leave completes
  expect(jump).toBeNull();
  expect(result.current.active?.session.sessionId).toBe("wbs_3");
  act(() => { jump = result.current.close(a.session, { abandoned: true, generation: a.generation }); }); // or its Abandon
  expect(jump).toBeNull();
  expect(result.current.active?.session.sessionId).toBe("wbs_3");
  expect(result.current.abandoned).toBeNull();
  // B's own Leave still leaves, at B's passage.
  const b = result.current.active!;
  act(() => { jump = result.current.close(b.session, { generation: b.generation }); });
  expect(jump).toBe("t6");
  expect(result.current.active).toBeNull();
});

it("R5: a departure from a workbench shown in an earlier generation (left, another book) changes nothing", async () => {
  api.workbenchOpen.mockResolvedValue({ version: 1, session: session(), resumed: true });
  const { result } = hook(book, null);
  await act(async () => result.current.resume("wbs_1"));
  const first = result.current.active!;
  act(() => { result.current.close(first.session, { generation: first.generation }); });
  await act(async () => result.current.resume("wbs_1")); // the same problem, shown again
  let jump: string | null = "unset";
  act(() => { jump = result.current.close(first.session, { generation: first.generation }); }); // the old view's late Leave
  expect(jump).toBeNull();
  expect(result.current.active?.session.sessionId).toBe("wbs_1");
});

// Fix round 5 audit: the marks' list answers in the order they were asked.
// An older refresh (the book's first) that lands after a newer one (after a
// Leave) never puts back the stale list.
it("round 5 audit: an older marks refresh landing late never replaces a newer one", async () => {
  const first = deferred<{ sessions: unknown[] }>();
  const newer = [{ sessionId: "wbs_1", status: "open" }];
  api.workbenchForSource.mockReturnValueOnce(first.promise).mockResolvedValue({ sessions: newer });
  api.workbenchOpen.mockResolvedValue({ version: 1, session: session(), resumed: true });
  const { result } = hook(book, null);
  await act(async () => result.current.resume("wbs_1"));
  const a = result.current.active!;
  await act(async () => { result.current.close(a.session, { generation: a.generation }); }); // the newer refresh
  await waitFor(() => expect(result.current.sessions).toEqual(newer));
  await act(async () => { first.resolve({ sessions: [] }); });
  expect(result.current.sessions).toEqual(newer);
});
