// RW2b + H3, the Codex review's frontend findings (docs/reviews/reader-rw2b-h3-codex-review.md):
// F5 help on a fresh problem with no saved step lands under the problem;
// F6 editing a checked step dims its marker at once, with no call;
// F7 leaving while a check is pending sends no delivering read and cancels it;
// F8 a failed save asks for no hint or suggestion and keeps the choice;
// F14 a hint's own claims are shown, each labelled.
import { act, cleanup, fireEvent, render, renderHook, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ComponentProps } from "react";
import { Workbench } from "./Workbench";
import { HELP_COPY, withLocalEdits } from "./helpModel";
import { UNSAVED_HELP, useWorkbenchHelp } from "./useWorkbenchHelp";
import { setAlgoConfig } from "../../app/algoConfig";
import type { CheckViewDto, WorkbenchSessionDto } from "../../api/dto";

const api = vi.hoisted(() => ({
  workbenchSaveStep: vi.fn(), workbenchSetBook: vi.fn(), workbenchLeave: vi.fn(), workbenchAbandon: vi.fn(),
  workbenchReopen: vi.fn(), workbenchRefreshImport: vi.fn(), workbenchBind: vi.fn(), workbenchRetryImport: vi.fn(),
  workbenchSubmit: vi.fn(), workbenchGet: vi.fn(),
  workbenchCheck: vi.fn(), workbenchSuggestHelp: vi.fn(), workbenchRequestHelp: vi.fn(), workbenchHelpJob: vi.fn(),
  workbenchCancelHelp: vi.fn(), workbenchAnswerDiscriminating: vi.fn(), workbenchSetHelpStyle: vi.fn(),
  workbenchHelpState: vi.fn(),
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => () => undefined, destroy: vi.fn() }) }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../render/LiveMarkdownEditor", async () => {
  const React = await import("react");
  return {
    LiveMarkdownEditor: (p: { value: string; onChange: (value: string) => void; ariaLabel?: string; focusSignal?: number }) => {
      const ref = React.useRef<HTMLTextAreaElement | null>(null);
      React.useEffect(() => { if (p.focusSignal) ref.current?.focus(); }, [p.focusSignal]);
      return <textarea ref={ref} aria-label={p.ariaLabel} value={p.value} onChange={(event) => p.onChange(event.target.value)} />;
    },
  };
});

const RECORD = { bookCounted: false, bookVisible: false, hints: 0, questionHints: 0, ownAttempt: true, line: "your own attempt",
  footer: "book hidden · help used: none", stuckNote: null };
const STEP_1 = "F(x) = x^2 on [0, 1]";

function session(overrides: Partial<WorkbenchSessionDto> = {}): WorkbenchSessionDto {
  return {
    sessionId: "wb1", practiceItemId: "pi_cdf", stemMd: "Find P(X <= 1/2).", importStatus: "none", importError: null,
    origin: "practice", entry: "practice_screen", parentSessionId: null, extractionId: null, spanIds: [], sourceVisible: false,
    sourceHiddenAt: null, sourceShownAt: null, practiceSessionId: null, helpStyle: null, status: "open", attemptId: null,
    createdAt: "2026-10-18T09:00:00Z", updatedAt: "2026-10-18T09:00:00Z", closedAt: null, lastEditedStepId: null,
    steps: [
      { stepId: "s1", chainId: "c1", ordinal: 1, kind: "step", bodyMd: STEP_1, deleted: false, createdAt: "x", editedAt: "x", versions: [] },
    ],
    record: RECORD, parts: null, sourceId: null, ...overrides,
  } as WorkbenchSessionDto;
}

function props(overrides: Partial<ComponentProps<typeof Workbench>> = {}): ComponentProps<typeof Workbench> {
  return { initial: session(), layout: "full", practiceSessionId: "ps1", onSession: vi.fn(), onLeave: vi.fn(),
    onAbandoned: vi.fn(), onSubmitted: vi.fn(), onError: vi.fn(), ...overrides };
}

const CHECK: CheckViewDto = {
  assistId: "ha_check", checkedAt: "2026-10-18T09:05:00Z", firstQuestionableStepId: null, errorKind: null,
  assumptions: [], symbolicAvailable: true, stale: false, changedSteps: [],
  verdicts: [{ chainId: "c1", number: 1, verdict: "valid", method: "checked", mark: "✓", label: "checked", reason: "",
    dependsOn: [], assumption: "", first: false, editedSinceCheck: false, deletedSinceCheck: false, checkedText: STEP_1 }],
};

const HINT_RESULT = {
  status: "ready", assistId: "ha_first", hintMd: "What is your first move?", kind: "approach_question", level: 1,
  labels: { origin: "AI-written", kind: "a question about your approach", workedHelp: null, horizon: null },
  replies: ["doesnt_connect", "book_way"], steps: { aboutStepId: null, aboutStep: null, continueFromStepId: null, continueFromStep: null, firstQuestionableStep: null },
  stepLine: "starts from the givens", shown: true, bridgeJobId: null, claims: [],
};

function done(result: unknown, jobId = "job") {
  return { version: 1, jobId, state: "done", result };
}

beforeEach(() => {
  vi.resetAllMocks();
  setAlgoConfig({ workbench: { enabled: true, help: { enabled: true, bridge: true, symbolic: true } }, hints: { adaptiveEnabled: true, helpStyle: "balanced" } });
  api.workbenchHelpState.mockResolvedValue({ version: 1, check: null, hints: [], helpStyle: null, storedHelpStyle: "balanced", hintsEnabled: true });
  let saved = 0;
  api.workbenchSaveStep.mockImplementation(async (input: { op: string; bodyMd?: string; kind?: string; stepId?: string }) => {
    saved += 1;
    return { version: 1, savedAt: "x", record: RECORD,
      step: { stepId: `row_${saved}`, chainId: input.stepId ?? `row_${saved}`, ordinal: saved, kind: input.kind ?? "step",
        bodyMd: input.bodyMd ?? "", deleted: input.op === "delete", createdAt: "x", editedAt: "x", versions: [] } };
  });
  api.workbenchCancelHelp.mockResolvedValue({ version: 1, jobId: "j1", state: "cancelled", cancelled: true, reason: null });
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  setAlgoConfig({});
});

it("F5: Help on a fresh problem with no saved step shows the ladder and the hint under the problem", async () => {
  api.workbenchSuggestHelp.mockResolvedValue(done({ status: "ready", suggestion: null, steps: HINT_RESULT.steps }, "sug"));
  api.workbenchRequestHelp.mockResolvedValue(done(HINT_RESULT, "hint"));
  render(<Workbench {...props({ initial: session({ steps: [] }) })} />);
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: /^help ·/ })); });
  const block = await screen.findByTestId("workbench-problem-help");
  expect(within(block).getByTestId("help-ladder")).toBeTruthy();
  expect(api.workbenchSuggestHelp).toHaveBeenCalledWith({ sessionId: "wb1", focusedStepId: null });
  await act(async () => { fireEvent.keyDown(within(block).getByTestId("help-ladder"), { key: "Enter" }); });
  await waitFor(() => expect(within(screen.getByTestId("workbench-problem-help")).getByTestId("workbench-hint")).toBeTruthy());
  expect(screen.getByTestId("workbench-hint").textContent).toContain("What is your first move?");
});

it("F6: editing a checked step dims its marker and says the check is older, with no call", async () => {
  api.workbenchHelpState.mockResolvedValue({ version: 1, check: CHECK, hints: [], helpStyle: null, storedHelpStyle: "balanced", hintsEnabled: true });
  render(<Workbench {...props()} />);
  await waitFor(() => expect(screen.getByTestId("workbench-verdict")).toBeTruthy());
  expect(screen.getByTestId("workbench-verdict").textContent).not.toContain(HELP_COPY.editedSinceCheck);
  fireEvent.change(screen.getByRole("textbox", { name: "Step 1" }), { target: { value: "F(x) = x^3 on [0, 1]" } });
  const marker = screen.getByTestId("workbench-verdict");
  expect(marker.textContent).toContain(HELP_COPY.editedSinceCheck);
  expect(marker.style.opacity).toBe("0.5");
  expect(screen.getByTestId("workbench-check-summary").textContent).toContain("step 1 has changed since");
  expect(api.workbenchCheck).not.toHaveBeenCalled();
});

it("F6: the comparison is pure and leaves an unedited check as it is", () => {
  expect(withLocalEdits(CHECK, [{ chainId: "c1", body: STEP_1 }])).toBe(CHECK);
  const edited = withLocalEdits(CHECK, [{ chainId: "c1", body: "x" }]);
  expect(edited?.verdicts[0].editedSinceCheck).toBe(true);
  expect(edited?.stale).toBe(true);
  expect(withLocalEdits(CHECK, [])?.verdicts[0].deletedSinceCheck).toBe(true);
});

function hookOptions(overrides: Partial<Parameters<typeof useWorkbenchHelp>[0]> = {}) {
  return { sessionId: "wb1", enabled: true, hintsEnabled: true, storedHelpStyle: "balanced" as const,
    beforeRequest: async () => true, onRecord: vi.fn(), ...overrides };
}

it("F7: leaving while a check is pending sends no delivering read and cancels the job", async () => {
  vi.useFakeTimers();
  api.workbenchCheck.mockResolvedValue({ version: 1, jobId: "j1", state: "pending", result: null });
  api.workbenchHelpJob.mockResolvedValue(done({ status: "ready", shown: true }, "j1"));
  const { result, unmount } = renderHook(() => useWorkbenchHelp(hookOptions()));
  await act(async () => {
    void result.current.runCheck();
    await Promise.resolve();
    await Promise.resolve();
  });
  expect(api.workbenchCheck).toHaveBeenCalled();
  unmount();
  await act(async () => { await vi.advanceTimersByTimeAsync(5000); });
  expect(api.workbenchHelpJob).not.toHaveBeenCalled();
  expect(api.workbenchCancelHelp).toHaveBeenCalledWith("j1");
});

it("F8: when the latest edits can't be saved, no hint or suggestion is asked for and the choice stays", async () => {
  const { result } = renderHook(() => useWorkbenchHelp(hookOptions({ beforeRequest: async () => false })));
  await act(async () => { result.current.openHelp("c1"); });
  await waitFor(() => expect(result.current.ladder.notice).toBe(UNSAVED_HELP));
  expect(api.workbenchSuggestHelp).not.toHaveBeenCalled();
  await act(async () => { await result.current.take(4); });
  expect(api.workbenchRequestHelp).not.toHaveBeenCalled();
  expect(result.current.ladder.open).toBe(true);
  expect(result.current.ladder.chosen).toBe(4);
  const hint = { assistId: "ha", kind: "next_step", level: 3, hintMd: "x", labels: {}, aboutStepId: "c1", continueFromStepId: null,
    stepLine: "", replies: ["book_way"], discriminatingAnswer: null, bridge: null };
  await act(async () => { await result.current.bookWay(hint); });
  expect(api.workbenchRequestHelp).not.toHaveBeenCalled();
  expect(result.current.notice?.message).toBe(UNSAVED_HELP);
});

it("F14: a hint's own claims are shown under it, each labelled checked or the model's reading", async () => {
  api.workbenchHelpState.mockResolvedValue({ version: 1, check: null, storedHelpStyle: "balanced", helpStyle: null, hintsEnabled: true,
    hints: [{ ...HINT_RESULT, assistId: "ha_claims", kind: "next_step", level: 3, hintMd: "Your step 1 stands.", aboutStepId: "c1",
      symbolicEnabled: true,
      continueFromStepId: null, discriminatingAnswer: null, bridge: null,
      claims: [
        { step: 1, statement: "step 1 is the antiderivative of the density", status: "checked", label: "checked", kind: "integration", reason: "" },
        { step: 1, statement: "step 1 stands as written", status: "model", label: "model's reading, not checked", kind: "", reason: "" },
      ] }] });
  render(<Workbench {...props()} />);
  const claims = await screen.findByTestId("workbench-hint-claims");
  expect(claims.textContent).toContain("✓ step 1 is the antiderivative of the density — checked");
  expect(claims.textContent).toContain("≈ step 1 stands as written — model's reading, not checked");
});

// RW2b fix round 11: the hint job's symbolicEnabled reaches the hint view, so
// a claim is "✓" only while the server says the switch is on.
it.each([[true, "✓ x + x = 2x — checked"], [false, "≈ x + x = 2x — model's reading, not checked"]])(
  "a hint job's claims follow the server's symbolic switch (%s)", async (enabled, line) => {
    const claims = [{ step: 1, statement: "x + x = 2x", status: "checked", label: "checked", kind: "equivalence", reason: "" }];
    api.workbenchSuggestHelp.mockResolvedValue(done({ status: "ready", suggestion: null, steps: HINT_RESULT.steps }, "sug"));
    api.workbenchRequestHelp.mockResolvedValue(done({ ...HINT_RESULT, claims, symbolicEnabled: enabled }, "hint"));
    render(<Workbench {...props({ initial: session({ steps: [] }) })} />);
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: /^help ·/ })); });
    const block = await screen.findByTestId("workbench-problem-help");
    await act(async () => { fireEvent.keyDown(within(block).getByTestId("help-ladder"), { key: "Enter" }); });
    const shown = await screen.findByTestId("workbench-hint-claims");
    expect(shown.textContent).toContain(line);
  });
