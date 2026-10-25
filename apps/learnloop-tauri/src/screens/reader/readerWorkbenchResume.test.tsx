// UX Phase 3 (docs/specs/ux_learnloop_v1.md §7.1 threads, §10 3.3): Today's
// "resume ▸" on an unfinished problem. The shell opens the problem's book and
// hands the workbench a resume request; once that book is the one open, the
// hook asks the one explicit resume (RW2a's, by the problem's id), once, and
// the shell forgets that request by identity. Another book open waits.
import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import type { SourceLibraryCard, WorkbenchSessionDto } from "../../api/dto";
import { useReaderWorkbench, type ReaderWorkbenchResume } from "./useReaderWorkbench";

const { api } = vi.hoisted(() => ({ api: { workbenchOpen: vi.fn(), workbenchForSource: vi.fn(), workbenchAdmit: vi.fn() } }));
vi.mock("../../api/client", () => ({ api }));

const book = { sourceId: "src_prob", title: "Probability", canonicalUri: "p.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard;
const other = { ...book, sourceId: "src_other", title: "Other" } as SourceLibraryCard;
const extractionOf = (card: SourceLibraryCard) => (card.sourceId === "src_prob" ? "ext_prob" : "ext_other");

function session(extra: Partial<WorkbenchSessionDto> = {}): WorkbenchSessionDto {
  return {
    sessionId: "wb_1", practiceItemId: null, stemMd: "Exercise 5.9", importStatus: "none", importError: null, origin: "reader",
    entry: "work_through", parentSessionId: null, extractionId: "ext_prob", spanIds: ["sp12"], sourceVisible: false, sourceHiddenAt: null,
    sourceShownAt: null, practiceSessionId: null, helpStyle: null, status: "open", attemptId: null, createdAt: "t", updatedAt: "t",
    closedAt: null, steps: [], lastEditedStepId: null, record: {} as WorkbenchSessionDto["record"], parts: null, sourceId: "src_prob",
    ...extra,
  };
}

beforeEach(() => {
  api.workbenchOpen.mockReset();
  api.workbenchForSource.mockReset();
  api.workbenchForSource.mockResolvedValue({ sessions: [] });
});

function hook(card: SourceLibraryCard, request: ReaderWorkbenchResume | null) {
  const onResumeShown = vi.fn();
  const onError = vi.fn();
  const rendered = renderHook(
    ({ card: open, request: wanted }) => useReaderWorkbench({
      enabled: true, extractionId: extractionOf(open), card: open, onError,
      props: { resumeProblem: wanted, onResumeShown },
    }),
    { initialProps: { card, request } },
  );
  return { ...rendered, onResumeShown, onError };
}

it("resumes the problem once its own book is open, and the shell forgets that request", async () => {
  api.workbenchOpen.mockResolvedValue({ version: 1, session: session(), resumed: true });
  const request = { sessionId: "wb_1", sourceId: "src_prob" };
  const { result, rerender, onResumeShown } = hook(other, request);
  await act(async () => undefined);
  expect(api.workbenchOpen).not.toHaveBeenCalled(); // another book is open: it waits
  rerender({ card: book, request });
  await waitFor(() => expect(api.workbenchOpen).toHaveBeenCalledTimes(1));
  expect(api.workbenchOpen.mock.calls[0][0]).toEqual({ origin: "reader", entry: "resume", sessionId: "wb_1", extractionId: "ext_prob" });
  await waitFor(() => expect(result.current.active?.session.sessionId).toBe("wb_1"));
  expect(onResumeShown).toHaveBeenCalledWith(request);
  // The same request again changes nothing.
  rerender({ card: book, request });
  await act(async () => undefined);
  expect(api.workbenchOpen).toHaveBeenCalledTimes(1);
});

it("without a request, nothing is resumed", async () => {
  const { result } = hook(book, null);
  await act(async () => undefined);
  expect(api.workbenchOpen).not.toHaveBeenCalled();
  expect(result.current.active).toBeNull();
});
