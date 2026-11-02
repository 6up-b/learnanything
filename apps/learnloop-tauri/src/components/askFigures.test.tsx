// Reader RW5d P3 (spec_reader_show_me_figures_v1 §6.4, §11.3, §11.4): "show me ▸"
// in the CA2 Ask panel on practice, feedback and the workbench, with its cost
// line said before sending; the take step on a check on your own; the hint
// chooser's "a figure to explore" line. Off (no `ask.figures`), the panel is
// CA2's exactly.
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { setAlgoConfig } from "../app/algoConfig";
import { AskOverlay, type AskTarget } from "./AskOverlay";
import { figureCostLine, figureHostRef, PANEL_FIGURE_COPY } from "./askFigures";

const { api } = vi.hoisted(() => ({ api: {
  getTutorTranscript: vi.fn(), askTutorQuestion: vi.fn(), previewTutorOpening: vi.fn(),
  getLearnerTextGap: vi.fn(), reverseLearnerTextGap: vi.fn(), setHelpStyle: vi.fn(),
  figureRequest: vi.fn(), readerFigureJob: vi.fn(), figureTakeStep: vi.fn(), figureOpen: vi.fn(),
  readerFigureRevise: vi.fn(), readerFigurePredict: vi.fn(), readerFigureExplain: vi.fn(), figureRichCancel: vi.fn()
} }));
vi.mock("../api/client", () => ({ api }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));
vi.mock("./OpenInSource", () => ({ OpenInSource: () => null }));
vi.mock("../screens/reader/figures/FigureInline", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../screens/reader/figures/FigureInline")>()),
  FigureInline: ({ figure, ctl }: { figure: { figureId: string; fuller?: unknown }; ctl: { revise: (figure: unknown, note: string) => void } }) => (
    <>
      <div data-testid="figure-inline" data-fuller={figure.fuller ? "1" : "0"}>{figure.figureId}</div>
      <button type="button" onClick={() => ctl.revise(figure, "bigger")}>test-revise</button>
    </>
  )
}));

const PANEL = { ask: { panelEnabled: true, helpStyle: "balanced", coldHelpConverts: true, figures: true } };
const FIGURE = {
  figureId: "fig_1", extractionId: null, spanIds: [], anchorSpanId: null, region: null, origin: "ask",
  verification: "illustrative", kind: "illustrative", label: "AI-built illustration", reason: null,
  unsupportedKind: null, supersedesId: null, revisionNote: null, versions: 1, createdAt: "2026-11-01T00:00:00Z",
  specJson: "{}", demonstrates: "the area grows", assumptions: [], predictions: [], propertyChecks: [],
  goalText: "the area under 2x", goalAuthor: "learner", grounding: "none", passages: []
};

function job(help: Record<string, unknown>) {
  return { version: 1, jobId: "ljob_1", kind: "figure_build", askId: null, state: "done",
           result: { figure: FIGURE, reused: false, help } };
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  setAlgoConfig(PANEL);
  api.getTutorTranscript.mockResolvedValue({ events: [], remaining: 3, earlier: [], earlierCountsAsHint: true,
                                             cold: false, helpStyle: "balanced" });
  api.figureRequest.mockResolvedValue(job({ host: "practice", countsAsHint: true, status: "counted", new: true,
                                             line: PANEL_FIGURE_COPY.counts }));
});
afterEach(() => {
  cleanup();
  setAlgoConfig({});
});

const PRACTICE: AskTarget = {
  context: "practice", practiceItemId: "pi_1", sessionId: "s1", submissionId: "serve-2",
  attemptProgress: "draft_started", readDraft: () => "my draft", itemLabel: "Exercise 6.1.12"
};

async function openDocked(target: AskTarget = PRACTICE, props: Partial<Parameters<typeof AskOverlay>[0]> = {}) {
  render(<AskOverlay variant="docked" target={target} onClose={vi.fn()} onToast={vi.fn()} {...props} />);
  await waitFor(() => expect(api.getTutorTranscript).toHaveBeenCalledOnce());
  return screen.getByTestId("ask-panel-docked");
}

function type(text: string) {
  const input = screen.getByLabelText("ask in your words");
  fireEvent.change(input, { target: { value: text } });
  return input;
}

it("says what a figure costs on each host before sending", () => {
  expect(figureCostLine({ context: "feedback", attemptId: "a1" }, false, false)).toBe(PANEL_FIGURE_COPY.free);
  expect(figureCostLine(PRACTICE, false, false)).toBe(PANEL_FIGURE_COPY.counts);
  expect(figureCostLine(PRACTICE, true, false)).toBe(PANEL_FIGURE_COPY.cold);
  expect(figureCostLine(PRACTICE, true, true)).toBe(PANEL_FIGURE_COPY.counts);
  expect(figureHostRef(PRACTICE)).toEqual({ itemId: "pi_1", submissionId: "serve-2", sessionId: "s1" });
  expect(figureHostRef({ ...PRACTICE, workbenchSessionId: "wb1" })).toEqual({ itemId: "pi_1", workbenchSessionId: "wb1" });
  expect(figureHostRef({ context: "feedback", attemptId: "a1" })).toEqual({ attemptId: "a1" });
});

it("show me ▸ sends the words as a figure goal on the attempt and lands the figure at panel width", async () => {
  const onFigureEvent = vi.fn();
  const panel = await openDocked(PRACTICE, { onFigureEvent });
  expect(within(panel).getByTestId("ask-figure-cost").textContent).toContain(PANEL_FIGURE_COPY.counts);
  type("the area under 2x");
  fireEvent.click(within(panel).getByText(PANEL_FIGURE_COPY.send));
  await waitFor(() => expect(screen.getByTestId("figure-inline").textContent).toBe("fig_1"));
  expect(api.figureRequest).toHaveBeenCalledWith({
    goalText: "the area under 2x", origin: "ask", takeStepToken: null,
    hostRef: { itemId: "pi_1", submissionId: "serve-2", sessionId: "s1" }
  });
  expect(api.askTutorQuestion).not.toHaveBeenCalled();
  expect(api.figureTakeStep).not.toHaveBeenCalled();
  const line = screen.getByTestId("ask-figure-line");
  expect(line.textContent).toContain(PANEL_FIGURE_COPY.countsLine);
  fireEvent.click(within(line).getByText(PANEL_FIGURE_COPY.widen));
  expect(screen.getByTestId("ask-figure-frame").getAttribute("data-wide")).toBe("1");
  expect(onFigureEvent).toHaveBeenCalledWith({ counted: true, converted: false });
});

it("alt+↵ is show me; ↵ still asks", async () => {
  await openDocked();
  const input = type("the area under 2x");
  fireEvent.keyDown(input, { key: "Enter", altKey: true });
  await waitFor(() => expect(api.figureRequest).toHaveBeenCalledOnce());
  expect(api.askTutorQuestion).not.toHaveBeenCalled();
});

it("on a check on your own, sending is the take step: it converts first, then the request carries its token", async () => {
  api.figureTakeStep.mockResolvedValue({ needed: true, token: "ha_take", banner: PANEL_FIGURE_COPY.banner });
  const onFigureEvent = vi.fn();
  const panel = await openDocked({ ...PRACTICE, coldCheck: true }, { onFigureEvent });
  expect(within(panel).getByTestId("ask-figure-cost").textContent).toContain(PANEL_FIGURE_COPY.cold);
  type("the area under 2x");
  fireEvent.click(within(panel).getByText(PANEL_FIGURE_COPY.send));
  await waitFor(() => expect(api.figureRequest).toHaveBeenCalledOnce());
  expect(api.figureTakeStep).toHaveBeenCalledWith({ itemId: "pi_1", submissionId: "serve-2", sessionId: "s1",
                                                    workbenchSessionId: null });
  expect(api.figureTakeStep.mock.invocationCallOrder[0]).toBeLessThan(api.figureRequest.mock.invocationCallOrder[0]);
  expect(api.figureRequest.mock.calls[0][0]).toMatchObject({ takeStepToken: "ha_take" });
  expect(onFigureEvent).toHaveBeenCalledWith({ counted: true, converted: true, banner: PANEL_FIGURE_COPY.banner });
  // The next figure in the converted attempt carries the same token, with no second take step.
  type("the density and its CDF");
  fireEvent.click(within(panel).getByText(PANEL_FIGURE_COPY.send));
  await waitFor(() => expect(api.figureRequest).toHaveBeenCalledTimes(2));
  expect(api.figureTakeStep).toHaveBeenCalledOnce();
  await waitFor(() => expect(within(panel).getByTestId("ask-figure-cost").textContent).toContain(PANEL_FIGURE_COPY.counts));
});

it("feedback's show me is free and names the attempt", async () => {
  api.figureRequest.mockResolvedValue(job({ host: "feedback", countsAsHint: false, status: "free" }));
  const panel = await openDocked({ context: "feedback", attemptId: "att_1", practiceItemId: "pi_1" });
  expect(within(panel).getByTestId("ask-figure-cost").textContent).toContain(PANEL_FIGURE_COPY.free);
  type("the area under 2x");
  fireEvent.click(within(panel).getByText(PANEL_FIGURE_COPY.send));
  await waitFor(() => expect(screen.getByTestId("ask-figure-line").textContent).toContain(PANEL_FIGURE_COPY.freeLine));
  expect(api.figureRequest.mock.calls[0][0].hostRef).toEqual({ attemptId: "att_1" });
});

it("a figure that couldn't be recorded on the attempt is not shown", async () => {
  api.figureRequest.mockResolvedValue({ ...job({ host: "practice", status: "not_recorded" }),
                                        result: { figure: null, reused: false, help: { host: "practice", status: "not_recorded" } } });
  const panel = await openDocked();
  type("the area under 2x");
  fireEvent.click(within(panel).getByText(PANEL_FIGURE_COPY.send));
  await waitFor(() => expect(screen.getByTestId("ask-figure-line").textContent).toContain(PANEL_FIGURE_COPY.notRecorded));
  expect(screen.queryByTestId("figure-inline")).toBeNull();
});

it("switched off (no ask.figures), the panel has no show me and alt+↵ asks", async () => {
  setAlgoConfig({ ask: { panelEnabled: true, helpStyle: "balanced", coldHelpConverts: true } });
  api.askTutorQuestion.mockResolvedValue({ version: 1, eventId: "e1", answerMd: "A", questionType: "clarification",
                                           facets: [], hintEquivalent: false, leakSuspected: false, citations: [],
                                           remaining: 2, answerMode: "help_me_reason" });
  const panel = await openDocked();
  expect(within(panel).queryByTestId("ask-figure-cost")).toBeNull();
  expect(within(panel).queryByText(PANEL_FIGURE_COPY.send)).toBeNull();
  const input = type("What does V mean?");
  fireEvent.keyDown(input, { key: "Enter", altKey: true });
  await waitFor(() => expect(api.askTutorQuestion).toHaveBeenCalledOnce());
  expect(api.figureRequest).not.toHaveBeenCalled();
});

it("the chooser's explore_figure hint is one line that opens its figure on the attempt (§11.4)", async () => {
  const { HintPanel } = await import("../screens/practice/HintPanel");
  api.figureOpen.mockResolvedValue({ figure: FIGURE, help: { host: "practice", countsAsHint: true, status: "counted", new: false } });
  const entry = {
    key: "h1",
    result: { status: "ready", assistId: "ha_fig", kind: "explore_figure", level: 2, hintMd: "a figure to explore: vary the cut point",
              labels: { origin: "AI-written", kind: "a figure to explore" }, replies: [],
              figure: { figureId: "fig_1", label: "a figure to explore", goalText: "vary the cut point" } }
  };
  const hints = { entries: [entry], pending: false, notice: null, picks: [], saveHelpStyle: vi.fn(), press: vi.fn() };
  render(<HintPanel hints={hints as never} answer="" helpStyle="balanced" figureTarget={PRACTICE} />);
  const line = screen.getByTestId("hint-explore-figure");
  expect(line.textContent).toContain(PANEL_FIGURE_COPY.explore);
  expect(line.textContent).toContain("vary the cut point");
  fireEvent.click(within(line).getByText(PANEL_FIGURE_COPY.open));
  await waitFor(() => expect(screen.getByTestId("figure-inline").textContent).toBe("fig_1"));
  expect(api.figureOpen).toHaveBeenCalledWith({ figureId: "fig_1", takeStepToken: null,
                                               hostRef: { itemId: "pi_1", submissionId: "serve-2", sessionId: "s1" } });
});

// Reader RW5d P3, Codex review F4.

it("not right? asks the new version on the host the figure is open on now (F4)", async () => {
  api.readerFigureRevise.mockResolvedValue(job({ host: "practice", countsAsHint: true, status: "counted", new: false }));
  const panel = await openDocked();
  type("the area under 2x");
  fireEvent.click(within(panel).getByText(PANEL_FIGURE_COPY.send));
  await waitFor(() => expect(screen.getByTestId("figure-inline").textContent).toBe("fig_1"));
  fireEvent.click(screen.getByText("test-revise"));
  await waitFor(() => expect(api.readerFigureRevise).toHaveBeenCalledOnce());
  expect(api.readerFigureRevise).toHaveBeenCalledWith({ figureId: "fig_1", note: "bigger", takeStepToken: null,
                                                       hostRef: { itemId: "pi_1", submissionId: "serve-2", sessionId: "s1" } });
});

// Ruling R1 (landing step 0): figures on an attempt host are grammar and sketch only.

it("a figure lands on the attempt without its fuller version, and nothing rich is read or polled (R1)", async () => {
  const fuller = { ...FIGURE, figureId: "fig_full", tier: "manim" };
  api.figureRequest.mockResolvedValue({ ...job({ host: "practice", countsAsHint: true, status: "counted", new: true }),
                                        result: { figure: { ...FIGURE, fuller: { state: "ready", tier: "manim", phase: null, reason: null, richJobId: "rj_1", figure: fuller } },
                                                  reused: false, help: { host: "practice", countsAsHint: true, status: "counted", new: true } } });
  const panel = await openDocked();
  type("the area under 2x");
  fireEvent.click(within(panel).getByText(PANEL_FIGURE_COPY.send));
  await waitFor(() => expect(screen.getByTestId("figure-inline").textContent).toBe("fig_1"));
  expect(screen.getByTestId("figure-inline").dataset.fuller).toBe("0");
  await new Promise((resolve) => setTimeout(resolve, 50));
  expect(api.figureOpen).not.toHaveBeenCalled();
  expect(api.figureRichCancel).not.toHaveBeenCalled();
});

it("a build answering only a rich pending line is not a figure here and is never polled (R1)", async () => {
  const rich = { requestId: "fr_1", extractionId: null, anchorSpanId: null, tier: "manim", goalText: "the spiral",
                 state: "pending", phase: "writing", reason: null, richJobId: "rj_1" };
  api.figureRequest.mockResolvedValue({ version: 1, jobId: "ljob_1", kind: "figure_build", askId: null, state: "done",
                                        result: { figure: null, reused: false, rich, help: { host: "practice", countsAsHint: true } } });
  const panel = await openDocked();
  type("the spiral");
  fireEvent.click(within(panel).getByText(PANEL_FIGURE_COPY.send));
  await waitFor(() => expect(screen.getByTestId("ask-figure-line").dataset.state).toBe("failed"));
  expect(screen.getByTestId("ask-figure-line").querySelector("[data-rich-pending]")).toBeNull();
  expect(screen.queryByTestId("figure-inline")).toBeNull();
  await new Promise((resolve) => setTimeout(resolve, 50));
  expect(api.figureOpen).not.toHaveBeenCalled();
});
