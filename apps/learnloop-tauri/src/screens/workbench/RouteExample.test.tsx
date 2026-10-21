// Reader workbench RW2c (spec §5.10, G39, G40; UX §5.6): the worked example
// in the learner's route under its hint and on "show me a similar example",
// "another passage" under a bridge or an example whose draw kept options, and
// the switch-off pin: with the app config carrying none of RW2c's keys the
// workbench renders RW2b's hints and makes no RW2c call (the api mock names
// only RW2b's calls plus RW2c's, and RW2c's must stay untouched).
import { act, cleanup, fireEvent, render, renderHook, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ComponentProps } from "react";
import { Workbench } from "./Workbench";
import { EXAMPLE_COPY, useRouteExamples } from "./RouteExample";
import { algoConfig, setAlgoConfig } from "../../app/algoConfig";
import type { WorkbenchHintViewDto, WorkbenchSessionDto } from "../../api/dto";

const api = vi.hoisted(() => ({
  workbenchSaveStep: vi.fn(), workbenchSetBook: vi.fn(), workbenchLeave: vi.fn(), workbenchAbandon: vi.fn(),
  workbenchReopen: vi.fn(), workbenchRefreshImport: vi.fn(), workbenchBind: vi.fn(), workbenchRetryImport: vi.fn(),
  workbenchSubmit: vi.fn(), workbenchGet: vi.fn(),
  workbenchCheck: vi.fn(), workbenchSuggestHelp: vi.fn(), workbenchRequestHelp: vi.fn(), workbenchHelpJob: vi.fn(),
  workbenchCancelHelp: vi.fn(), workbenchAnswerDiscriminating: vi.fn(), workbenchSetHelpStyle: vi.fn(),
  workbenchHelpState: vi.fn(),
  // RW2c's.
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

function session(overrides: Partial<WorkbenchSessionDto> = {}): WorkbenchSessionDto {
  return {
    sessionId: "wb1", practiceItemId: "pi_cdf", stemMd: "Find P(X <= 1/2).", importStatus: "none", importError: null,
    origin: "reader", entry: "work_through", parentSessionId: null, extractionId: "ext", spanIds: [], sourceVisible: false,
    sourceHiddenAt: null, sourceShownAt: null, practiceSessionId: null, helpStyle: null, status: "open", attemptId: null,
    createdAt: "2026-10-21T09:00:00Z", updatedAt: "2026-10-21T09:00:00Z", closedAt: null, lastEditedStepId: null,
    steps: [
      { stepId: "s1", chainId: "c1", ordinal: 1, kind: "step", bodyMd: "F(x) = x^2 on [0, 1]", deleted: false, createdAt: "x", editedAt: "x", versions: [] },
    ],
    record: RECORD, parts: null, sourceId: null, ...overrides,
  } as WorkbenchSessionDto;
}

function props(overrides: Partial<ComponentProps<typeof Workbench>> = {}): ComponentProps<typeof Workbench> {
  return { initial: session(), layout: "full", practiceSessionId: "ps1", onSession: vi.fn(), onLeave: vi.fn(),
    onAbandoned: vi.fn(), onSubmitted: vi.fn(), onError: vi.fn(), onPeekPassage: vi.fn(), ...overrides };
}

const EXAMPLE = {
  assistId: "ha_ex", line: "A worked example that takes your route: Book A · §3.4 · compare it with your step 1",
  spanId: "w2", extractionId: "ext", label: "Book A · §3.4", verdict: "follows_learner_route", trigger: "after_hint",
  aboutStepId: "c1", hintAssistId: "ha_hint", alternatives: 1, optionId: "ext:w2", drawAssistId: "ha_ex",
};

function hint(overrides: Partial<WorkbenchHintViewDto> = {}): WorkbenchHintViewDto {
  return {
    assistId: "ha_hint", kind: "worked_parallel", level: 3, hintMd: "Take the CDF first.",
    labels: { origin: "AI-written", kind: "a worked parallel", workedHelp: null, horizon: null } as WorkbenchHintViewDto["labels"],
    aboutStepId: "c1", continueFromStepId: null, stepLine: "about step 1", replies: ["doesnt_connect"], discriminatingAnswer: null,
    bridge: { assistId: "ha_bridge", line: "§ compare with the book: Book · §5.1", spanId: "s1", extractionId: "ext", label: "Book · §5.1",
      alternatives: 2, optionId: "ext:s1", drawAssistId: "ha_bridge" },
    claims: [], ...overrides,
  };
}

function helpState(extra: Record<string, unknown> = {}) {
  return { version: 1, check: null, hints: [hint({ example: EXAMPLE })], helpStyle: null, storedHelpStyle: "balanced",
    hintsEnabled: true, ...extra };
}

function configWith(rw2c: Record<string, boolean>) {
  setAlgoConfig({ workbench: { enabled: true, help: { enabled: true, bridge: true, symbolic: true, ...rw2c } },
    hints: { adaptiveEnabled: true, helpStyle: "balanced" } });
}

beforeEach(() => {
  vi.resetAllMocks();
  api.workbenchSaveStep.mockResolvedValue({ version: 1, record: RECORD });
});

afterEach(() => {
  cleanup();
  setAlgoConfig({});
});

it("off: with none of RW2c's keys the workbench is RW2b's and makes no RW2c call", async () => {
  configWith({});
  expect(algoConfig().workbenchHelp).toEqual({ bridge: true, symbolic: true });
  api.workbenchHelpState.mockResolvedValue(helpState({ examplesAvailable: true, examples: [EXAMPLE] }));
  render(<Workbench {...props()} />);
  await screen.findByText("§ compare with the book: Book · §5.1");
  expect(screen.queryByTestId("workbench-route-example")).toBeNull();
  expect(screen.queryByTestId("workbench-passage-extras")).toBeNull();
  expect(screen.queryByTestId("workbench-show-example")).toBeNull();
  expect(screen.queryByText(EXAMPLE_COPY.another)).toBeNull();
  expect(api.workbenchShowExample).not.toHaveBeenCalled();
  expect(api.workbenchAnotherPassage).not.toHaveBeenCalled();
});

it("on: the restored example sits under its hint and opens its passage in the book", async () => {
  configWith({ examples: true, passageDraw: true });
  expect(algoConfig().workbenchHelp).toEqual({ bridge: true, symbolic: true, examples: true, passageDraw: true });
  api.workbenchHelpState.mockResolvedValue(helpState());
  const onPeekPassage = vi.fn();
  render(<Workbench {...props({ onPeekPassage })} />);
  const line = await screen.findByTestId("workbench-route-example");
  expect(line.textContent).toBe(EXAMPLE.line);
  expect(line.getAttribute("data-verdict")).toBe("follows_learner_route");
  fireEvent.click(line);
  expect(onPeekPassage).toHaveBeenCalledWith("w2");
});

it("another passage under an example and under a bridge shows the next option, with no search", async () => {
  configWith({ examples: true, passageDraw: true });
  api.workbenchHelpState.mockResolvedValue(helpState());
  api.workbenchAnotherPassage.mockImplementation(async ({ assistId }: { assistId: string }) => (assistId === "ha_ex"
    ? { version: 1, kind: "example", passage: { ...EXAMPLE, assistId: "ha_pick_ex", spanId: "w3", line: "A worked example that takes your route: Book A · §3.6" } }
    : { version: 1, kind: "bridge", passage: { ...EXAMPLE, assistId: "ha_pick_br", spanId: "s2", line: "§ compare with the book: Book · §5.2", alternatives: 2, verdict: null } }));
  render(<Workbench {...props()} />);
  fireEvent.click(await screen.findByTestId("workbench-another-passage"));
  await screen.findByText("A worked example that takes your route: Book A · §3.6");
  expect(api.workbenchAnotherPassage).toHaveBeenCalledWith({ sessionId: "wb1", assistId: "ha_ex" });
  fireEvent.click(screen.getByTestId("workbench-another-bridge"));
  await screen.findByText("§ compare with the book: Book · §5.2");
  expect(api.workbenchAnotherPassage).toHaveBeenCalledWith({ sessionId: "wb1", assistId: "ha_bridge" });
  // A second click asks from the passage now shown (the pick's own row).
  fireEvent.click(screen.getByTestId("workbench-another-bridge"));
  await waitFor(() => expect(api.workbenchAnotherPassage).toHaveBeenLastCalledWith({ sessionId: "wb1", assistId: "ha_pick_br" }));
  expect(api.workbenchShowExample).not.toHaveBeenCalled();
  expect(api.workbenchHelpJob).not.toHaveBeenCalled();
});

it("with the draw off there is no another passage, though the example shows", async () => {
  configWith({ examples: true });
  api.workbenchHelpState.mockResolvedValue(helpState());
  render(<Workbench {...props()} />);
  await screen.findByTestId("workbench-route-example");
  expect(screen.queryByTestId("workbench-another-bridge")).toBeNull();
  expect(screen.getByText("§ compare with the book: Book · §5.1")).toBeTruthy();
});

it("show me a similar example runs on the step in focus and lands under the steps", async () => {
  configWith({ examples: true });
  api.workbenchHelpState.mockResolvedValue({ ...helpState(), hints: [], examplesAvailable: true, examples: [] });
  api.workbenchShowExample.mockResolvedValue({ version: 1, jobId: "job_ex", kind: "example", state: "done",
    result: { status: "ready", shown: true, assistId: "ha_show", line: "A worked example (by another route): Book B · p. 12",
      spanId: "w9", extractionId: "ext", label: "Book B · p. 12", verdict: "worked_example", trigger: "show_me", aboutStepId: "c1" } });
  render(<Workbench {...props()} />);
  fireEvent.click(await screen.findByText(EXAMPLE_COPY.showMe));
  await screen.findByText("A worked example (by another route): Book B · p. 12");
  expect(api.workbenchShowExample).toHaveBeenCalledWith({ sessionId: "wb1", focusedStepId: "c1" });
});

it("show me is not offered where the server says examples are unavailable (no S3, not a Reader problem)", async () => {
  configWith({ examples: true });
  api.workbenchHelpState.mockResolvedValue({ ...helpState(), hints: [], examplesAvailable: false, examples: [] });
  render(<Workbench {...props()} />);
  await waitFor(() => expect(api.workbenchHelpState).toHaveBeenCalled());
  expect(screen.queryByText(EXAMPLE_COPY.showMe)).toBeNull();
});

it("a hint's example job is followed to its passage; nothing found stays quiet under the hint", async () => {
  configWith({ examples: true });
  api.workbenchHelpJob
    .mockResolvedValueOnce({ version: 1, jobId: "job_a", kind: "example", state: "done",
      result: { status: "ready", shown: true, assistId: "ha_a", line: "A worked example that takes your route: Book A · §3.4",
        spanId: "w2", extractionId: "ext", label: "Book A · §3.4", verdict: "follows_learner_route", trigger: "after_hint", aboutStepId: "c1" } })
    .mockResolvedValueOnce({ version: 1, jobId: "job_b", kind: "example", state: "done", result: { status: "none", line: EXAMPLE_COPY.none } });
  const { result } = renderHook(() => useRouteExamples({ sessionId: "wb1", examples: true, passageDraw: false }));
  act(() => result.current.followExample("ha_hint_a", "job_a"));
  await waitFor(() => expect(result.current.underHint.ha_hint_a?.status).toBe("ready"));
  expect(result.current.underHint.ha_hint_a?.view?.spanId).toBe("w2");
  act(() => result.current.followExample("ha_hint_b", "job_b"));
  await waitFor(() => expect(api.workbenchHelpJob).toHaveBeenCalledTimes(2));
  await waitFor(() => expect(result.current.underHint.ha_hint_b).toBeUndefined());
});

it("the hook does nothing while both switches are off", () => {
  const { result } = renderHook(() => useRouteExamples({ sessionId: "wb1", examples: false, passageDraw: false }));
  expect(result.current.active).toBe(false);
  act(() => result.current.followExample("ha", "job"));
  act(() => result.current.restore({ version: 1, check: null, hints: [hint({ example: EXAMPLE })], helpStyle: null,
    storedHelpStyle: "balanced", hintsEnabled: true, examplesAvailable: true }));
  expect(result.current.underHint).toEqual({});
  expect(result.current.available).toBe(false);
  expect(api.workbenchHelpJob).not.toHaveBeenCalled();
});
