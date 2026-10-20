// RW4b fix round 4, R5 (Codex final verify F9, as written): exercise A's open
// is pending; the learner chooses exercise B while B's book loads; A's answer
// arrives. The shell's queued exercise is consumed by identity, so A's
// completion never clears B, and B opens on its own book.
import { act, renderHook, waitFor } from "@testing-library/react";
import { useState } from "react";
import { beforeEach, expect, it, vi } from "vitest";
import type { SourceLibraryCard, WorkbenchSessionDto } from "../../api/dto";
import * as shell from "../../app/readerWorkbench";
import type { ReaderWorkbenchExercise } from "./exerciseCandidates";
import { useReaderWorkbench } from "./useReaderWorkbench";

const { api } = vi.hoisted(() => ({ api: { workbenchOpen: vi.fn(), workbenchForSource: vi.fn(), workbenchAdmit: vi.fn() } }));
vi.mock("../../api/client", () => ({ api }));

const bookA = { sourceId: "src_a", title: "A", canonicalUri: "a.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard;
const bookB = { ...bookA, sourceId: "src_b", title: "B" } as SourceLibraryCard;
const exercise = (book: "a" | "b"): ReaderWorkbenchExercise => ({
  key: `srcex:ext_${book}:t1`, sourceId: `src_${book}`, extractionId: `ext_${book}`, spanIds: ["t1"], stemMd: `${book}: solve`,
  entry: "practice_this", proposalId: "pp_1", sourceExercise: { proposalId: "pp_1", extractionId: `ext_${book}`, spanIds: ["t1"] },
});
const A = exercise("a");
const B = exercise("b");
function opened(of: ReaderWorkbenchExercise): WorkbenchSessionDto {
  return { sessionId: `wbs_${of.sourceId}`, practiceItemId: null, stemMd: of.stemMd, importStatus: "pending", importError: null,
    origin: "reader", entry: "practice_this", parentSessionId: null, extractionId: of.extractionId, spanIds: of.spanIds, sourceVisible: false,
    sourceHiddenAt: null, sourceShownAt: null, practiceSessionId: null, helpStyle: null, status: "open", attemptId: null, createdAt: "t",
    updatedAt: "t", closedAt: null, steps: [], lastEditedStepId: null, record: {} as WorkbenchSessionDto["record"], parts: null,
    sourceId: of.sourceId } as WorkbenchSessionDto;
}

beforeEach(() => {
  api.workbenchOpen.mockReset();
  api.workbenchForSource.mockReset();
  api.workbenchForSource.mockResolvedValue({ sessions: [] });
});

it("R5 (verify F9): an older exercise's open never clears a newer exercise queued since", async () => {
  let releaseA!: () => void;
  const gateA = new Promise<void>((resolve) => { releaseA = resolve; });
  api.workbenchOpen.mockImplementation(async (params: { extractionId: string }) => {
    if (params.extractionId === "ext_a") await gateA;
    return { version: 1, session: opened(params.extractionId === "ext_a" ? A : B), resumed: false };
  });
  const onExerciseShown = vi.fn();
  const { result, rerender } = renderHook(({ card, extractionId }) => {
    // The shell's slot, consumed as App.tsx consumes it.
    const [queued, setQueued] = useState<ReaderWorkbenchExercise | null>(A);
    const workbench = useReaderWorkbench({ enabled: true, extractionId, card, onError: vi.fn(), props: {
      exercise: queued,
      onExerciseShown: (shown) => { onExerciseShown(shown); setQueued((current) => shell.consumeShown(current, shown)); },
    } });
    return { workbench, queued, choose: setQueued };
  }, { initialProps: { card: bookA, extractionId: "ext_a" as string | null } });
  await waitFor(() => expect(api.workbenchOpen).toHaveBeenCalledTimes(1)); // A's open, pending
  act(() => result.current.choose(B)); // the learner chooses B...
  rerender({ card: bookB, extractionId: null }); // ...while B's book loads
  await act(async () => { releaseA(); await gateA; });
  expect(result.current.queued).toBe(B); // A's late answer cleared nothing
  expect(onExerciseShown).not.toHaveBeenCalledWith(B);
  rerender({ card: bookB, extractionId: "ext_b" }); // B's book is open
  await waitFor(() => expect(result.current.workbench.active?.session.sessionId).toBe("wbs_src_b"));
  expect(api.workbenchOpen.mock.calls.map(([params]) => params.extractionId)).toEqual(["ext_a", "ext_b"]);
  expect(onExerciseShown).toHaveBeenLastCalledWith(B);
  expect(result.current.queued).toBeNull();
});
