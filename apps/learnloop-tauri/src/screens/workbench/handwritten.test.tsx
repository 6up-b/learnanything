// Handwritten work as workbench steps (owner decision 2026-11-23): a line's text binds to a step under a key derived
// from the line, so a reopened problem finds the step it already has (never a second one), and a later text is an
// edit of that step. The hook alone, its writes through a faked workbench service.
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { WorkbenchSessionDto } from "../../api/dto";
import { useWorkbenchSession } from "./useWorkbenchSession";

const api = vi.hoisted(() => ({ workbenchSaveStep: vi.fn(), workbenchSetBook: vi.fn() }));
vi.mock("../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => () => undefined, destroy: vi.fn() }) }));

const RECORD = { bookCounted: false, bookVisible: true, hints: 0, questionHints: 0, ownAttempt: true, line: "your own attempt", footer: "", stuckNote: null };

function session(steps: WorkbenchSessionDto["steps"] = []): WorkbenchSessionDto {
  return {
    sessionId: "wb1", practiceItemId: "pi", stemMd: "Show it.", importStatus: "none", importError: null, origin: "reader", entry: "work_through",
    parentSessionId: null, extractionId: "ext", spanIds: [], sourceVisible: true, sourceHiddenAt: null, sourceShownAt: null, practiceSessionId: null,
    helpStyle: null, status: "open", attemptId: null, createdAt: "t", updatedAt: "t", closedAt: null, steps, lastEditedStepId: null,
    record: RECORD, parts: null, sourceId: "src",
  } as WorkbenchSessionDto;
}

const step = (stepId: string, chainId: string, bodyMd: string) => ({ stepId, chainId, ordinal: 1, kind: "step" as const, bodyMd, deleted: false, createdAt: "t", editedAt: "t", versions: [] });

beforeEach(() => {
  api.workbenchSaveStep.mockReset();
});
afterEach(() => cleanup());

it("a reopened problem finds its line's step again: one step, bound to the line, never a second", async () => {
  api.workbenchSaveStep.mockImplementation(async (input) => ({ step: step("row_old", "row_old", "$x$"), savedAt: "t", record: RECORD, input }));
  const { result } = renderHook(() => useWorkbenchSession(session([step("row_old", "row_old", "$x$")]), { onError: vi.fn() }));
  act(() => result.current.bindLine("blk_1", "$x$"));
  await waitFor(() => expect(api.workbenchSaveStep).toHaveBeenCalledTimes(1));
  expect(api.workbenchSaveStep.mock.calls[0][0]).toMatchObject({ op: "add", clientIdempotencyKey: "ink-step:blk_1", bodyMd: "$x$" });
  await waitFor(() => expect(result.current.boundLines.get("blk_1")).toBe("row_old"));
  expect(result.current.steps.filter((each) => !each.deleted).map((each) => [each.key, each.body])).toEqual([["row_old", "$x$"]]);
});

it("a later text of the line is an edit of its step, and a line with no text is never written", async () => {
  api.workbenchSaveStep.mockImplementation(async (input) => ({
    step: input.op === "add" ? step("row_1", "row_1", String(input.bodyMd)) : step("row_2", "row_1", String(input.bodyMd)), savedAt: "t", record: RECORD }));
  const { result } = renderHook(() => useWorkbenchSession(session(), { onError: vi.fn() }));
  act(() => result.current.bindLine("blk_2", "   "));
  expect(api.workbenchSaveStep).not.toHaveBeenCalled();
  act(() => result.current.bindLine("blk_2", "$p_k = -h_k$"));
  await waitFor(() => expect(result.current.boundLines.get("blk_2")).toBeDefined());
  await waitFor(() => expect(api.workbenchSaveStep).toHaveBeenCalledTimes(1));
  // The empty first step the problem opened with gave way to the line.
  expect(result.current.steps.map((each) => each.body)).toEqual(["$p_k = -h_k$"]);
  act(() => result.current.bindLine("blk_2", "$p_k = e^{h_k}/Z$"));
  await waitFor(() => expect(api.workbenchSaveStep).toHaveBeenCalledTimes(2), { timeout: 2000 });
  expect(api.workbenchSaveStep.mock.calls[1][0]).toMatchObject({ op: "edit", stepId: "row_1", bodyMd: "$p_k = e^{h_k}/Z$" });
});
