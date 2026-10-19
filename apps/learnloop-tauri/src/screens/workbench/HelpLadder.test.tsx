// RW2b's checks and help ladder in the workbench (spec §5.2-5.5; UX §4.10,
// §5.4-5.8, W5-W7): the ladder shows all five rungs at once, every one
// takeable; digits and arrows choose and only Enter takes; the suggested rung
// gets ▸ and *suggested (why?)* when the chooser returns, naming its form,
// and a split judgment says so; without a judgment the why says so too. A
// check lands as markers labelled by method, the first questionable step's
// reason and the model's guess, and the footer names it. A hint lands under
// the step it is about, its label naming kind, rung, the step it is about
// and the step it continues from; "doesn't connect" offers four shortcuts,
// a step picker and *where this goes*. Nothing that lands moves focus.
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

// -- the ladder on its own -----------------------------------------------------------------------

function ladderState(overrides: Partial<LadderState> = {}): LadderState {
  return { open: true, focusedStepId: "c2", chosen: 1, touched: false, suggestion: null, rungs: DEFAULT_RUNGS, pending: true, steps: null, notice: null, ...overrides };
}

it("shows all five rungs at once, each with its consequence, and none disabled for being too early", () => {
  render(<HelpLadder ladder={ladderState()} onChoose={vi.fn()} onTake={vi.fn()} onClose={vi.fn()} />);
  const rungs = [1, 2, 3, 4, 5].map((level) => screen.getByTestId(`ladder-rung-${level}`));
  expect(rungs.map((rung) => rung.getAttribute("aria-disabled"))).toEqual([null, null, null, null, null]);
  expect(rungs[3].textContent).toContain("worked help ◌");
  expect(rungs[0].textContent).toContain("hint");
  // Until the chooser answers, there is no suggestion and the ladder still works.
  expect(screen.queryByTestId("ladder-suggested")).toBeNull();
});

it("chooses with digits and arrows and takes only with Enter, so a stray key never reveals a worked step", () => {
  const onChoose = vi.fn();
  const onTake = vi.fn();
  render(<HelpLadder ladder={ladderState({ chosen: 2 })} onChoose={onChoose} onTake={onTake} onClose={vi.fn()} />);
  const list = screen.getByTestId("help-ladder");
  fireEvent.keyDown(list, { key: "5" });
  fireEvent.keyDown(list, { key: "ArrowDown" });
  expect(onChoose.mock.calls).toEqual([[5], [3]]);
  expect(onTake).not.toHaveBeenCalled();
  fireEvent.keyDown(list, { key: "Enter" });
  expect(onTake).toHaveBeenCalledWith(2);
});

it("marks the suggested rung with its form in plain words, and why? gives the inputs and a split judgment", () => {
  render(<HelpLadder ladder={ladderState({ suggestion: SUGGESTION, rungs: SUGGESTION.rungs, chosen: 3, pending: false })}
    onChoose={vi.fn()} onTake={vi.fn()} onClose={vi.fn()} />);
  expect(screen.getByTestId("ladder-suggested").textContent).toContain("suggested: 3 · a goal to aim for, about two steps ahead");
  expect(screen.getByTestId("ladder-rung-3").getAttribute("data-suggested")).toBe("true");
  expect(screen.getByTestId("ladder-rung-1").textContent).toContain("a question that tells apart two explanations of step 2");
  expect(screen.getByTestId("ladder-rung-1").textContent).toContain("not graded · counts as a hint");
  fireEvent.click(screen.getByRole("button", { name: /why\?/ }));
  expect(screen.getByTestId("ladder-why").textContent).toContain("LearnLoop's judgment");
  expect(screen.getByTestId("ladder-why").textContent).toContain("it leaned between a goal to aim for and the next step");
});

it("without a judgment the suggestion's why says so (the Reader's progression)", () => {
  const fallback = { ...SUGGESTION, chooser: "fallback" as const, level: 2, kind: "localize", why: "no judgment available right now — the next rung up", split: null, kindLabel: "where it stops holding", horizonLabel: null };
  render(<HelpLadder ladder={ladderState({ suggestion: fallback, chosen: 2, pending: false })} onChoose={vi.fn()} onTake={vi.fn()} onClose={vi.fn()} />);
  fireEvent.click(screen.getByRole("button", { name: /why\?/ }));
  expect(screen.getByTestId("ladder-why").textContent).toContain("no judgment available right now — the next rung up");
});

// -- in the workbench ------------------------------------------------------------------------------

it("Check my work says what it costs, lands as markers by method, and the footer names the check, without moving focus", async () => {
  api.workbenchCheck.mockResolvedValue(done({ status: "ready", assistId: "ha_check", shown: true, check: CHECK,
    record: { ...RECORD, hints: 1, ownAttempt: false, line: "1 hint (a check) → practice with help ◌ (not yet checked on your own)", footer: "book hidden · help used: a check" } }));
  render(<Workbench {...props()} />);
  const button = screen.getByRole("button", { name: /check my work · counts as a hint · ctrl\+k/ });
  const before = document.activeElement;
  await act(async () => { fireEvent.click(button); });
  await waitFor(() => expect(screen.getAllByTestId("workbench-verdict")).toHaveLength(2));
  const [first, second] = screen.getAllByTestId("workbench-verdict");
  expect(first.textContent).toContain("✓ checked");
  expect(second.textContent).toContain("? first");
  expect(screen.getByTestId("workbench-first-questionable").textContent).toContain("(model's guess)");
  expect(screen.getByTestId("workbench-check-summary").textContent).toContain("assumptions this uses: X has density 2x on [0, 1]");
  expect(screen.getByText(/help used: a check/)).toBeTruthy();
  expect(screen.getByTestId("workbench-record").textContent).toContain("1 hint (a check)");
  expect(document.activeElement).toBe(before);
  // Never red, never a score.
  expect(document.body.innerHTML).not.toMatch(/score/i);
});

it("Help opens the ladder below the step; the suggestion lands; Enter takes it and the hint sits under its step", async () => {
  api.workbenchSuggestHelp.mockResolvedValue(done({ status: "ready", suggestion: SUGGESTION, steps: HINT_RESULT.steps }, "sug"));
  api.workbenchRequestHelp.mockResolvedValue(done(HINT_RESULT, "hint"));
  render(<Workbench {...props()} />);
  fireEvent.focus(screen.getByRole("textbox", { name: "Step 2" }));
  await act(async () => { fireEvent.keyDown(screen.getByRole("region", { name: "workbench" }), { key: "h", ctrlKey: true }); });
  await waitFor(() => expect(screen.getByTestId("ladder-suggested")).toBeTruthy());
  expect(api.workbenchSuggestHelp).toHaveBeenCalledWith({ sessionId: "wb1", focusedStepId: "c2" });
  await act(async () => { fireEvent.keyDown(screen.getByTestId("help-ladder"), { key: "Enter" }); });
  await waitFor(() => expect(screen.getByTestId("workbench-hint")).toBeTruthy());
  expect(api.workbenchRequestHelp).toHaveBeenCalledWith(expect.objectContaining({ sessionId: "wb1", request: "more", takenLevel: 3, offeredLevel: 3, suggestionId: "j1" }));
  const hint = screen.getByTestId("workbench-hint");
  // Under step 2, the step it is about.
  expect(hint.closest("li")?.getAttribute("data-step-key")).toBe("c2");
  expect(hint.textContent).toContain("check this part · level 3 · on your step 2 · continues from step 1");
  expect(screen.getByTestId("workbench-record").textContent).toContain("1 hint (a level-3 hint)");
});

it("this doesn't connect offers four shortcuts that say what they do, a step picker on the hint's step, and where this goes", async () => {
  api.workbenchHelpState.mockResolvedValue({ version: 1, check: null, storedHelpStyle: "balanced", helpStyle: null, hintsEnabled: true,
    hints: [{ assistId: "ha_hint", kind: "error_specific", level: 3, hintMd: "Check step 2.", labels: HINT_RESULT.labels, aboutStepId: "c2",
      continueFromStepId: "c1", stepLine: HINT_RESULT.stepLine, replies: ["doesnt_connect", "book_way"], discriminatingAnswer: null, bridge: null }] });
  api.workbenchRequestHelp.mockResolvedValue(done({ ...HINT_RESULT, assistId: "ha_next", steps: { ...HINT_RESULT.steps, aboutStepId: "c1", aboutStep: 1 } }, "next"));
  render(<Workbench {...props()} />);
  await waitFor(() => expect(screen.getByTestId("workbench-hint")).toBeTruthy());
  fireEvent.click(screen.getByRole("button", { name: HELP_COPY.doesntConnect }));
  const box = screen.getByTestId("workbench-feedback");
  for (const shortcut of WORKBENCH_SHORTCUTS) expect(within(box).getByRole("button", { name: shortcut.label })).toBeTruthy();
  expect((within(box).getByRole("combobox", { name: "about step" }) as HTMLSelectElement).value).toBe("c2");
  fireEvent.click(within(box).getByRole("button", { name: "that's not where I'm stuck" }));
  expect(box.textContent).toContain("the next hint moves to the step you pick");
  fireEvent.change(within(box).getByRole("combobox", { name: "about step" }), { target: { value: "c1" } });
  fireEvent.click(within(box).getByRole("button", { name: HELP_COPY.whereThisGoes }));
  expect(box.textContent).toContain(WHERE_THIS_GOES.doesntConnect.line);
  await act(async () => { fireEvent.click(within(box).getByRole("button", { name: HELP_COPY.nextHint })); });
  expect(api.workbenchRequestHelp).toHaveBeenCalledWith(expect.objectContaining({ request: "feedback", answeredAssistId: "ha_hint",
    feedbackShortcut: "not_where_stuck", feedbackStepId: "c1" }));
});

it("the help style in the header changes this problem only, and the stored preference means no override", async () => {
  api.workbenchSetHelpStyle.mockResolvedValue({ version: 1, helpStyle: "let_me_struggle", storedHelpStyle: "balanced" });
  render(<Workbench {...props()} />);
  const control = screen.getByTestId("workbench-help-style");
  expect(within(control).getByRole("radio", { name: "[balanced]" }).getAttribute("aria-checked")).toBe("true");
  await act(async () => { fireEvent.click(within(control).getByRole("radio", { name: "struggle" })); });
  expect(api.workbenchSetHelpStyle).toHaveBeenCalledWith({ sessionId: "wb1", helpStyle: "let_me_struggle" });
});

it("a stuck step says where its words go", () => {
  render(<Workbench {...props({ initial: session({ steps: [{ stepId: "s1", chainId: "c1", ordinal: 1, kind: "stuck", bodyMd: "lost", deleted: false, createdAt: "x", editedAt: "x", versions: [] }] }) })} />);
  fireEvent.click(screen.getByRole("button", { name: HELP_COPY.whereThisGoes }));
  expect(screen.getByText(WHERE_THIS_GOES.stuck.line)).toBeTruthy();
});

it("switched off, the workbench has no check, no help and no confidence row", () => {
  setAlgoConfig({ workbench: { enabled: true }, hints: { adaptiveEnabled: true } });
  render(<Workbench {...props()} />);
  expect(screen.queryByRole("button", { name: /check my work/ })).toBeNull();
  expect(screen.queryByRole("button", { name: /^help ·/ })).toBeNull();
  expect(screen.queryByTestId("workbench-confidence")).toBeNull();
  expect(api.workbenchHelpState).not.toHaveBeenCalled();
});

// -- labels -----------------------------------------------------------------------------------------

it("a hint's label names its kind, rung, the step it is about and the step it continues from on one line", () => {
  expect(hintLabel({ labels: { origin: "AI-written", kind: "a goal to aim for", horizon: "about two steps ahead" }, level: 3, kind: "waypoint",
    stepLine: "on your step 3 · continues from step 2" }))
    .toBe("◇ model · a goal to aim for · about two steps ahead · level 3 · on your step 3 · continues from step 2");
  expect(hintLabel({ labels: { origin: "from the item", kind: "from the item" }, level: 3, kind: "authored", stepLine: "on your step 1 · starts from the givens" }))
    .toBe("from the item · level 3 · on your step 1 · starts from the givens");
  expect(hintLabel({ labels: { origin: "AI-written", kind: "a question that tells apart two explanations" }, level: 1, kind: "discriminating", stepLine: "" }))
    .toContain("not graded · counts as a hint");
});

it("every fixed line is free of judgments of the learner (G-H12) and every box says it never grades", () => {
  const lines = [...Object.values(HELP_COPY), ...WORKBENCH_SHORTCUTS.flatMap((entry) => [entry.label, entry.does]),
    ...Object.values(WHERE_THIS_GOES).map((entry) => entry.line), ...DEFAULT_RUNGS.map((rung) => rung.label)];
  for (const line of lines) for (const phrase of FORBIDDEN_WORDING) expect(line.toLowerCase()).not.toContain(phrase);
  for (const entry of Object.values(WHERE_THIS_GOES)) expect(entry.line.endsWith("never to grade you.")).toBe(true);
});

it("the optional confidence row before Submit is sent with the answer, and skipping it sends none", async () => {
  api.workbenchSubmit.mockResolvedValue({ version: 1, attempt: { attemptId: "a1" }, session: session({ status: "submitted" }), practiceSession: null });
  render(<Workbench {...props()} />);
  const row = screen.getByTestId("workbench-confidence");
  fireEvent.click(within(row).getByRole("radio", { name: "4" }));
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: /submit · ctrl\+↵/ })); });
  await waitFor(() => expect(api.workbenchSubmit).toHaveBeenCalled());
  expect(api.workbenchSubmit.mock.calls[0][0]).toMatchObject({ sessionId: "wb1", answerConfidence: 4 });
  // Never counted: the submit sends no hint count of its own.
  expect(api.workbenchSubmit.mock.calls[0][0]).not.toHaveProperty("hintsUsed");
});

it("focusing a checked step lightly outlines the steps it depends on", async () => {
  api.workbenchHelpState.mockResolvedValue({ version: 1, check: CHECK, hints: [], helpStyle: null, storedHelpStyle: "balanced", hintsEnabled: true });
  const { container } = render(<Workbench {...props()} />);
  await waitFor(() => expect(screen.getAllByTestId("workbench-verdict")).toHaveLength(2));
  fireEvent.focus(screen.getByRole("textbox", { name: "Step 2" }));
  await waitFor(() => expect(container.querySelector('[data-step-key="c1"]')?.getAttribute("data-depended-on")).toBe("true"));
  expect(container.querySelector('[data-step-key="c2"]')?.getAttribute("data-depended-on")).toBeNull();
});
