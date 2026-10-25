// Owner capture 2026-10-25 (B2): a ladder suggestion is a judgment made
// under the help style of that moment. Changing the style in the header while
// the ladder is open asks for the suggestion again under the new style (the
// sidecar also refuses to reuse a suggestion judged under another style).
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ComponentProps } from "react";
import { HelpLadder } from "./HelpLadder";
import { Workbench } from "./Workbench";
import { DEFAULT_RUNGS, FORBIDDEN_WORDING, HELP_COPY, WHERE_THIS_GOES, WORKBENCH_SHORTCUTS, hintLabel } from "./helpModel";
import type { LadderState } from "./useWorkbenchHelp";
import { setAlgoConfig } from "../../app/algoConfig";
import type { HelpSuggestionDto, WorkbenchSessionDto } from "../../api/dto";

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

function session(overrides: Partial<WorkbenchSessionDto> = {}): WorkbenchSessionDto {
  return {
    sessionId: "wb1", practiceItemId: "pi_cdf", stemMd: "Find P(X <= 1/2).", importStatus: "none", importError: null,
    origin: "practice", entry: "practice_screen", parentSessionId: null, extractionId: null, spanIds: [], sourceVisible: false,
    sourceHiddenAt: null, sourceShownAt: null, practiceSessionId: null, helpStyle: null, status: "open", attemptId: null,
    createdAt: "2026-10-18T09:00:00Z", updatedAt: "2026-10-18T09:00:00Z", closedAt: null, lastEditedStepId: null,
    steps: [
      { stepId: "s1", chainId: "c1", ordinal: 1, kind: "step", bodyMd: "F(x) = x^2 on [0, 1]", deleted: false, createdAt: "x", editedAt: "x", versions: [] },
      { stepId: "s2", chainId: "c2", ordinal: 2, kind: "step", bodyMd: "so P = F(1/2) + 1", deleted: false, createdAt: "x", editedAt: "x", versions: [] },
    ],
    record: RECORD, parts: null, sourceId: null, ...overrides,
  } as WorkbenchSessionDto;
}

function props(overrides: Partial<ComponentProps<typeof Workbench>> = {}): ComponentProps<typeof Workbench> {
  return { initial: session(), layout: "full", practiceSessionId: "ps1", onSession: vi.fn(), onLeave: vi.fn(),
    onAbandoned: vi.fn(), onSubmitted: vi.fn(), onError: vi.fn(), ...overrides };
}

const CHECK = {
  assistId: "ha_check", checkedAt: "2026-10-18T09:05:00Z", firstQuestionableStepId: "c2",
  errorKind: { kind: "conceptual", label: "looks like a concept applied the wrong way (model's guess)", reason: "" },
  assumptions: ["X has density 2x on [0, 1]"], symbolicAvailable: true, symbolicEnabled: true, stale: false, changedSteps: [],
  verdicts: [
    { chainId: "c1", number: 1, verdict: "valid", method: "checked", mark: "✓", label: "checked", reason: "", dependsOn: [], assumption: "", first: false, editedSinceCheck: false, deletedSinceCheck: false },
    { chainId: "c2", number: 2, verdict: "questionable", method: "model", mark: "?", label: "model's reading, not checked", reason: "a CDF value is already a probability — “F(1/2) + 1”", dependsOn: ["c1"], assumption: "", first: true, editedSinceCheck: false, deletedSinceCheck: false },
  ],
};

const SUGGESTION: HelpSuggestionDto = {
  level: 3, kind: "waypoint", chooser: "decider", horizonIndex: 1, propensity: 0.6, suggestionId: "j1", reason: null,
  why: "a goal to aim for, about two steps ahead: your steps so far stand; help style: balanced · LearnLoop's judgment",
  split: "it leaned between a goal to aim for and the next step",
  rungs: [{ ...DEFAULT_RUNGS[0], label: "a question that tells apart two explanations of step 2", discriminating: true }, ...DEFAULT_RUNGS.slice(1)],
  kindLabel: "a goal to aim for", horizonLabel: "about two steps ahead",
};

const HINT_RESULT = {
  status: "ready", assistId: "ha_hint", hintMd: "Steps 1 stand. Check the constant in step 2.", kind: "error_specific", level: 3,
  labels: { origin: "AI-written", kind: "check this part", workedHelp: null, horizon: null }, replies: ["doesnt_connect", "book_way"],
  steps: { aboutStepId: "c2", aboutStep: 2, continueFromStepId: "c1", continueFromStep: 1, firstQuestionableStep: 2 },
  stepLine: "on your step 2 · continues from step 1", shown: true, bridgeJobId: null,
  record: { ...RECORD, hints: 1, ownAttempt: false, line: "1 hint (a level-3 hint) → practice with help ◌ (not yet checked on your own)", footer: "book hidden · help used: a level-3 hint" },
};

function done(result: unknown, jobId = "job") {
  return { version: 1, jobId, state: "done", result };
}

beforeEach(() => {
  vi.resetAllMocks();
  setAlgoConfig({ workbench: { enabled: true, help: { enabled: true, bridge: true, symbolic: true } }, hints: { adaptiveEnabled: true, helpStyle: "balanced" } });
  api.workbenchHelpState.mockResolvedValue({ version: 1, check: null, hints: [], helpStyle: null, storedHelpStyle: "balanced", hintsEnabled: true });
  api.workbenchSaveStep.mockResolvedValue({ version: 1, savedAt: "x", record: RECORD, step: { stepId: "s9", chainId: "c9", ordinal: 9, kind: "step", bodyMd: "", deleted: false, createdAt: "x", editedAt: "x", versions: [] } });
});
afterEach(() => {
  cleanup();
  setAlgoConfig({});
});


it("B2: changing the help style while the ladder is open asks for a new suggestion", async () => {
  api.workbenchSuggestHelp.mockResolvedValue(done({ status: "ready", suggestion: SUGGESTION, steps: null }, "sug"));
  api.workbenchSetHelpStyle.mockResolvedValue({ version: 1, helpStyle: "guide_me", storedHelpStyle: "balanced" });
  render(<Workbench {...props()} />);
  fireEvent.focus(screen.getByRole("textbox", { name: "Step 2" }));
  await act(async () => { fireEvent.keyDown(screen.getByRole("region", { name: "workbench" }), { key: "h", ctrlKey: true }); });
  await waitFor(() => expect(screen.getByTestId("ladder-suggested")).toBeTruthy());
  expect(api.workbenchSuggestHelp).toHaveBeenCalledTimes(1);
  const control = screen.getByTestId("workbench-help-style");
  await act(async () => { fireEvent.click(within(control).getByRole("radio", { name: "guide" })); });
  await waitFor(() => expect(api.workbenchSuggestHelp).toHaveBeenCalledTimes(2));
  expect(api.workbenchSuggestHelp).toHaveBeenLastCalledWith({ sessionId: "wb1", focusedStepId: "c2" });
});

it("B2: with the ladder closed a style change asks for nothing", async () => {
  api.workbenchSetHelpStyle.mockResolvedValue({ version: 1, helpStyle: "guide_me", storedHelpStyle: "balanced" });
  render(<Workbench {...props()} />);
  const control = screen.getByTestId("workbench-help-style");
  await act(async () => { fireEvent.click(within(control).getByRole("radio", { name: "guide" })); });
  expect(api.workbenchSetHelpStyle).toHaveBeenCalled();
  expect(api.workbenchSuggestHelp).not.toHaveBeenCalled();
});

it("B1: the workbench reports its steps as the learner's work and offers Ask when the screen asks for it", async () => {
  const onAsk = vi.fn();
  const onWorkChange = vi.fn();
  render(<Workbench {...props({ onAsk, onWorkChange })} />);
  await waitFor(() => expect(onWorkChange).toHaveBeenLastCalledWith("1. F(x) = x^2 on [0, 1]\n2. so P = F(1/2) + 1"));
  fireEvent.click(screen.getByRole("button", { name: /^ask/ }));
  expect(onAsk).toHaveBeenCalledTimes(1);
});

it("B1: without the screen's Ask there is no Ask button (the Reader keeps its own)", () => {
  render(<Workbench {...props()} />);
  expect(screen.queryByRole("button", { name: /^ask/ })).toBeNull();
});
