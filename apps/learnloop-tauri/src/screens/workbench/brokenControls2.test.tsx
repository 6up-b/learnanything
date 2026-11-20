// UX-20 (UX journey audit part 2, workbench-1 #16-37): help levels 1 and 2 each ended "I couldn't write a hint that
// fits here; press Hint again or use the item's hint." The workbench has no Hint button and no item hint, and the
// line stayed beside the step through every later help. In the walk's vault both requests failed the hint writer's
// own checks twice (level 1 "approach_question_declares_nothing", level 2 "localize_no_quote" then
// "rule2_past_first_questionable"): the sidecar's message is the practice screen's, so the workbench says its own.
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { HELP_COPY } from "./helpModel";
import { useWorkbenchHelp } from "./useWorkbenchHelp";
import { findJargon } from "../../copy/denyList";

const api = vi.hoisted(() => ({
  workbenchCheck: vi.fn(), workbenchSuggestHelp: vi.fn(), workbenchRequestHelp: vi.fn(), workbenchHelpJob: vi.fn(),
  workbenchCancelHelp: vi.fn(), workbenchAnswerDiscriminating: vi.fn(), workbenchSetHelpStyle: vi.fn(), workbenchHelpState: vi.fn(),
}));
vi.mock("../../api/client", () => ({ api }));

const PRACTICE_SCREEN_LINE = "I couldn't write a hint that fits here; press Hint again or use the item's hint.";

function done(result: unknown, jobId = "job") {
  return { version: 1, jobId, state: "done", result };
}

function options() {
  return { sessionId: "wb1", enabled: true, hintsEnabled: true, storedHelpStyle: "balanced" as const,
    beforeRequest: async () => true, onRecord: vi.fn() };
}

beforeEach(() => {
  vi.resetAllMocks();
  api.workbenchHelpState.mockResolvedValue({ version: 1, check: null, hints: [], helpStyle: null, storedHelpStyle: "balanced", hintsEnabled: true });
  api.workbenchSuggestHelp.mockResolvedValue(done({ status: "ready", suggestion: null, steps: null }, "sug"));
});
afterEach(() => cleanup());

it("UX-20: a level no hint could be written for names this screen's controls, never a Hint button or the item's hint", async () => {
  api.workbenchRequestHelp.mockResolvedValue(done({ status: "unavailable", reason: "contract_failed", message: PRACTICE_SCREEN_LINE, shown: false }));
  const { result } = renderHook(() => useWorkbenchHelp(options()));
  await act(async () => { result.current.openHelp("c1"); });
  await act(async () => { await result.current.take(1); });
  const message = result.current.notice?.message ?? "";
  expect(message).toBe(HELP_COPY.noFittingHint);
  expect(message).toBe("Couldn't write a hint at this level that fits your work. Your steps are saved: press help to try again, or choose another level.");
  expect(message).not.toMatch(/Hint again|item's hint/);
  expect(findJargon(message)).toEqual([]);
});

it("UX-20: the same for a reply at level 1 or 2 with nothing left at that level", async () => {
  api.workbenchRequestHelp.mockResolvedValue(done({ status: "unavailable", reason: "no_option", message: PRACTICE_SCREEN_LINE, shown: false }));
  const { result } = renderHook(() => useWorkbenchHelp(options()));
  const hint = { assistId: "ha", kind: "approach_question", level: 1, hintMd: "x", labels: {}, aboutStepId: "c1", continueFromStepId: null,
    stepLine: "", replies: ["smaller_step"], discriminatingAnswer: null, bridge: null, claims: [], symbolicEnabled: false };
  await act(async () => { await result.current.smallerStep(hint); });
  expect(result.current.notice?.message).toBe(HELP_COPY.noFittingHint);
});

it("UX-20: other failures keep the sidecar's own words", async () => {
  api.workbenchRequestHelp.mockResolvedValue(done({ status: "unavailable", reason: "capped", message: "Today's hint budget is spent.", shown: false }));
  const { result } = renderHook(() => useWorkbenchHelp(options()));
  await act(async () => { await result.current.take(1); });
  expect(result.current.notice?.message).toBe("Today's hint budget is spent.");
});

it("UX-20: the failed line goes when the learner asks for help again: a check, or the help ladder", async () => {
  api.workbenchRequestHelp.mockResolvedValue(done({ status: "unavailable", reason: "contract_failed", message: PRACTICE_SCREEN_LINE, shown: false }));
  api.workbenchCheck.mockResolvedValue(done({ status: "ready", shown: true, check: null }, "chk"));
  const { result } = renderHook(() => useWorkbenchHelp(options()));
  await act(async () => { await result.current.take(1); });
  expect(result.current.notice).not.toBeNull();
  await act(async () => { await result.current.runCheck(); });
  expect(result.current.notice).toBeNull();
  await act(async () => { await result.current.take(2); });
  expect(result.current.notice).not.toBeNull();
  await act(async () => { result.current.openHelp("c1"); });
  await waitFor(() => expect(result.current.notice).toBeNull());
});
