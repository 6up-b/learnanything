// Reader workbench RW2c, fix round 2 (spec §5.10; UX §5.6):
//
// 7. A drawn bridge passage in another book (Book B) opens Book B: from the
//    bridge job's first result, and from a resumed problem whose last pick
//    was in Book B (the restored bridge keeps its book).
// 8. "show me a similar example" uses the save-before-help barrier: with a
//    save still failing it refuses and asks for nothing.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ComponentProps } from "react";
import { Workbench } from "./Workbench";
import { EXAMPLE_COPY } from "./RouteExample";
import { DEFAULT_RUNGS } from "./helpModel";
import { setAlgoConfig } from "../../app/algoConfig";
import type { HelpSuggestionDto, WorkbenchHintViewDto, WorkbenchSessionDto } from "../../api/dto";

const api = vi.hoisted(() => ({
  workbenchSaveStep: vi.fn(), workbenchSetBook: vi.fn(), workbenchLeave: vi.fn(), workbenchAbandon: vi.fn(),
  workbenchReopen: vi.fn(), workbenchRefreshImport: vi.fn(), workbenchBind: vi.fn(), workbenchRetryImport: vi.fn(),
  workbenchSubmit: vi.fn(), workbenchGet: vi.fn(),
  workbenchCheck: vi.fn(), workbenchSuggestHelp: vi.fn(), workbenchRequestHelp: vi.fn(), workbenchHelpJob: vi.fn(),
  workbenchCancelHelp: vi.fn(), workbenchAnswerDiscriminating: vi.fn(), workbenchSetHelpStyle: vi.fn(),
  workbenchHelpState: vi.fn(),
  workbenchShowExample: vi.fn(), workbenchAnotherPassage: vi.fn(),
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => () => undefined, destroy: vi.fn() }) }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../render/LiveMarkdownEditor", () => ({
  LiveMarkdownEditor: (p: { value: string; onChange: (value: string) => void; ariaLabel?: string }) => (
    <textarea aria-label={p.ariaLabel} value={p.value} onChange={(event) => p.onChange(event.target.value)} />
  ),
}));

const RECORD = { bookCounted: false, bookVisible: false, hints: 1, questionHints: 0, ownAttempt: false, line: "with help",
  footer: "book hidden · help used: 1", stuckNote: null };

function session(): WorkbenchSessionDto {
  return {
    sessionId: "wb1", practiceItemId: "pi_cdf", stemMd: "Find P(X <= 1/2).", importStatus: "none", importError: null,
    origin: "reader", entry: "work_through", parentSessionId: null, extractionId: "ext_a", spanIds: [], sourceVisible: false,
    sourceHiddenAt: null, sourceShownAt: null, practiceSessionId: null, helpStyle: null, status: "open", attemptId: null,
    createdAt: "2026-10-21T09:00:00Z", updatedAt: "2026-10-21T09:00:00Z", closedAt: null, lastEditedStepId: null,
    steps: [
      { stepId: "s1", chainId: "c1", ordinal: 1, kind: "step", bodyMd: "F(x) = x^2 on [0, 1]", deleted: false, createdAt: "x", editedAt: "x", versions: [] },
    ],
    record: RECORD, parts: null, sourceId: "src_a",
  } as WorkbenchSessionDto;
}

function props(overrides: Partial<ComponentProps<typeof Workbench>> = {}): ComponentProps<typeof Workbench> {
  return { initial: session(), layout: "full", practiceSessionId: "ps1", onSession: vi.fn(), onLeave: vi.fn(),
    onAbandoned: vi.fn(), onSubmitted: vi.fn(), onError: vi.fn(), onPeekPassage: vi.fn(), ...overrides };
}

const LABELS = { origin: "AI-written", kind: "a worked parallel", workedHelp: null, horizon: null } as WorkbenchHintViewDto["labels"];

function done(result: unknown, jobId = "job") {
  return { version: 1, jobId, state: "done", result };
}

const SUGGESTION: HelpSuggestionDto = {
  level: 3, kind: "worked_parallel", chooser: "decider", horizonIndex: 1, propensity: 0.6, suggestionId: "j1", reason: null,
  why: "a worked parallel", split: null, rungs: DEFAULT_RUNGS, kindLabel: "a worked parallel", horizonLabel: null,
};

beforeEach(() => {
  vi.resetAllMocks();
  setAlgoConfig({ workbench: { enabled: true, help: { enabled: true, bridge: true, symbolic: true, examples: true, passageDraw: true } },
    hints: { adaptiveEnabled: true, helpStyle: "balanced" } });
  api.workbenchSaveStep.mockResolvedValue({ version: 1, savedAt: "x", record: RECORD,
    step: { stepId: "s9", chainId: "c9", ordinal: 9, kind: "step", bodyMd: "", deleted: false, createdAt: "x", editedAt: "x", versions: [] } });
  api.workbenchHelpState.mockResolvedValue({ version: 1, check: null, hints: [], helpStyle: null, storedHelpStyle: "balanced",
    hintsEnabled: true, examplesAvailable: true, examples: [] });
});

afterEach(() => {
  cleanup();
  setAlgoConfig({});
});

it("7: a drawn bridge passage in Book B opens Book B from the bridge job's first result", async () => {
  api.workbenchSuggestHelp.mockResolvedValue(done({ status: "ready", suggestion: SUGGESTION, steps: null }, "sug"));
  api.workbenchRequestHelp.mockResolvedValue(done({
    status: "ready", assistId: "ha_hint", hintMd: "Take the CDF first.", kind: "worked_parallel", level: 3, labels: LABELS,
    replies: ["doesnt_connect"], steps: { aboutStepId: "c1", aboutStep: 1, continueFromStepId: null, continueFromStep: null, firstQuestionableStep: null },
    stepLine: "on your step 1", shown: true, bridgeJobId: "bjob", record: RECORD,
  }, "hint"));
  api.workbenchHelpJob.mockImplementation(async (jobId: string) => (jobId === "bjob"
    ? done({ status: "ready", shown: true, assistId: "ha_bridge", line: "§ compare with the book: Book B · §2.1",
      spanId: "s2", extractionId: "ext_b", sourceId: "src_b", label: "Book B · §2.1", alternatives: 1 }, "bjob")
    : done(null, jobId)));
  const onPeekPassage = vi.fn();
  render(<Workbench {...props({ onPeekPassage })} />);
  fireEvent.focus(screen.getByRole("textbox", { name: "Step 1" }));
  await act(async () => { fireEvent.keyDown(screen.getByRole("region", { name: "workbench" }), { key: "h", ctrlKey: true }); });
  await waitFor(() => expect(screen.getByTestId("ladder-suggested")).toBeTruthy());
  await act(async () => { fireEvent.keyDown(screen.getByTestId("help-ladder"), { key: "Enter" }); });
  const bridge = await screen.findByTestId("workbench-bridge");
  expect(bridge.textContent).toBe("§ compare with the book: Book B · §2.1");
  fireEvent.click(bridge);
  expect(onPeekPassage).toHaveBeenCalledWith("s2", { extractionId: "ext_b", sourceId: "src_b" });
});

it("7: a resumed problem whose last pick was in Book B opens Book B", async () => {
  api.workbenchHelpState.mockResolvedValue({ version: 1, check: null, helpStyle: null, storedHelpStyle: "balanced", hintsEnabled: true,
    examplesAvailable: true, examples: [], hints: [{
      assistId: "ha_hint", kind: "worked_parallel", level: 3, hintMd: "Take the CDF first.", labels: LABELS, aboutStepId: "c1",
      continueFromStepId: null, stepLine: "on your step 1", replies: ["doesnt_connect"], discriminatingAnswer: null, claims: [],
      bridge: { assistId: "ha_pick", line: "§ compare with the book: Book B · §2.3", spanId: "s3", extractionId: "ext_b",
        sourceId: "src_b", label: "Book B · §2.3", alternatives: 1, optionId: "ext_b:s3", drawAssistId: "ha_bridge" },
    }] });
  const onPeekPassage = vi.fn();
  render(<Workbench {...props({ onPeekPassage })} />);
  fireEvent.click(await screen.findByTestId("workbench-bridge"));
  expect(onPeekPassage).toHaveBeenCalledWith("s3", { extractionId: "ext_b", sourceId: "src_b" });
});

it("8: show me a similar example waits for the steps to save and refuses while a save is failing", async () => {
  api.workbenchSaveStep.mockRejectedValue({ code: "database_locked", message: "locked" });
  render(<Workbench {...props()} />);
  const box = screen.getByRole("textbox", { name: "Step 1" });
  fireEvent.focus(box);
  fireEvent.change(box, { target: { value: "F(x) = x^2, so P = F(1/2)" } });
  expect(await screen.findByText("not saved yet — retrying · your text is safe in this window", undefined, { timeout: 3000 })).toBeTruthy();
  fireEvent.click(await screen.findByText(EXAMPLE_COPY.showMe));
  await act(async () => { await new Promise((resolve) => setTimeout(resolve, 50)); });
  // Never a search against older, saved work than the learner sees.
  expect(api.workbenchShowExample).not.toHaveBeenCalled();
  expect(screen.getByText(/aren't saved yet, so no example was looked for/)).toBeTruthy();
});

it("8: with the steps saved, show me a similar example asks as before", async () => {
  api.workbenchShowExample.mockResolvedValue(done({ status: "ready", shown: true, assistId: "ha_show",
    line: "A worked example (by another route): Book B · p. 12", spanId: "w9", extractionId: "ext_b", sourceId: "src_b",
    label: "Book B · p. 12", verdict: "worked_example", trigger: "show_me", aboutStepId: "c1" }, "job_ex"));
  const onPeekPassage = vi.fn();
  render(<Workbench {...props({ onPeekPassage })} />);
  fireEvent.click(await screen.findByText(EXAMPLE_COPY.showMe));
  const line = await screen.findByText("A worked example (by another route): Book B · p. 12");
  expect(api.workbenchShowExample).toHaveBeenCalledWith({ sessionId: "wb1", focusedStepId: "c1" });
  fireEvent.click(line);
  expect(onPeekPassage).toHaveBeenCalledWith("w9", { extractionId: "ext_b", sourceId: "src_b" });
});
