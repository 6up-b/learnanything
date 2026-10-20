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

it("tells the shell once when the import binds the problem (running → admitted)", async () => {
  api.workbenchOpen.mockResolvedValue({ version: 1, session: session(), resumed: false });
  const { result, onExerciseAdmitted } = hook(book, EXERCISE);
  await waitFor(() => expect(result.current.active).not.toBeNull());
  act(() => result.current.update(session({ importStatus: "pending" })));
  expect(onExerciseAdmitted).not.toHaveBeenCalled(); // still running: nothing to pick yet
  const bound = session({ importStatus: "bound", practiceItemId: "pi_ex_1",
    sourceExercise: { proposalId: "pp_1", importId: "sei_1", importStatus: "written", reason: null, keyStatus: "model_answer", keyLabel: "Model's answer, not checked" } });
  act(() => result.current.update(bound));
  act(() => result.current.update(bound));
  expect(onExerciseAdmitted).toHaveBeenCalledTimes(1);
  expect(onExerciseAdmitted).toHaveBeenCalledWith({
    practiceItemId: "pi_ex_1", proposalId: "pp_1", importId: "sei_1", sourceId: "src_text", card: book, spanId: "t6",
    stemMd: EXERCISE.stemMd, workbenchSessionId: "wbs_1",
  });
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
  hook(book, { ...EXERCISE, proposalId: null, sourceExercise: undefined, importRequest: request, entry: "work_through" });
  await waitFor(() => expect(api.workbenchOpen).toHaveBeenCalledTimes(1));
  expect(api.workbenchOpen.mock.calls[0][0]).toMatchObject({ entry: "work_through", importRequest: request });
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
