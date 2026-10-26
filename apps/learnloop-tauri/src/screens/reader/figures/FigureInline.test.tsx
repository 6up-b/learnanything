// Reader RW5a: the inline figure (spec §8.1; UX §4.7, Moment 9, W11; G23, G24, G45, G54).
//
// Collapsed to one line with its verification label; one expanded at a time;
// the prediction before the first change with its before/after readout and
// "what changed?"; play only when pressed (step buttons under reduced motion),
// the same evaluation as the slider; the values table; "not right?"; nothing
// moves focus.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { FigurePredictionResultDto, FigureViewDto } from "../../../api/dto";
import corpus from "./figureGoldenCorpus.json";
import { FIGURE_COPY, FIGURE_FRAME, FiguresUnder, PROPERTY_CHECK_COPY } from "./FigureInline";
import { formatValue } from "./FigurePanels";
import { compileSpec, evaluateFigure, type FigureSpec } from "./figureSpec";
import { useFigures, type FiguresContract } from "./useFigures";

const api = vi.hoisted(() => ({
  readerFigures: vi.fn(), readerFigureRequest: vi.fn(), readerFigureJob: vi.fn(), readerFigureJobCancel: vi.fn(),
  readerFigureRevise: vi.fn(), readerFigurePredict: vi.fn(), readerFigureExplain: vi.fn(), readerLogActivity: vi.fn(),
}));
vi.mock("../../../api/client", () => ({ api }));

const FLAGSHIP = corpus.figures.find((item) => item.id === "two_sided_exponential")!.spec as unknown as FigureSpec;
const CONTRACT: FiguresContract = { predictions: true, region: true, revisions: true };

function figureView(overrides: Partial<FigureViewDto> = {}): FigureViewDto {
  return {
    figureId: "fig_1", extractionId: "ext_prob", spanIds: ["p3"], anchorSpanId: "p3", region: null, origin: "selection",
    verification: "verified", kind: "reconstructed", label: "AI-built · matches the book's equation (checked)",
    reason: null, unsupportedKind: null, supersedesId: null, revisionNote: null, versions: 1,
    createdAt: "2026-10-21T00:00:00", specJson: JSON.stringify(FLAGSHIP),
    demonstrates: FLAGSHIP.demonstrates, assumptions: [{ text: "λ > 0 and 0 < p < 1", spanId: "p2", quote: "0 < p < 1" }],
    predictions: [
      { index: 0, prompt: "If λ doubles, what happens to P(X ≤ 0)?", kind: "direction", answered: null,
        choices: [{ value: "rises", label: "it rises" }, { value: "falls", label: "it falls" }, { value: "same", label: "it stays the same" }] },
    ],
    ...overrides,
  };
}

function Harness({ spans, contract = CONTRACT }: { spans: string[]; contract?: FiguresContract }) {
  const ctl = useFigures({ extractionId: "ext_prob", contract });
  return (
    <div>
      <button type="button">elsewhere</button>
      {spans.map((span) => <div key={span} data-span={span}><FiguresUnder ctl={ctl} spanId={span} /></div>)}
      <button type="button" onClick={() => ctl.request({ spanIds: ["p2"] })}>make p2 explorable</button>
    </div>
  );
}

beforeEach(() => {
  vi.resetAllMocks();
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [figureView()] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

it("is collapsed to one line with its code-owned badge, and expands in place", async () => {
  render(<Harness spans={["p3"]} />);
  const line = await screen.findByRole("button", { name: /interactive version/ });
  expect(line.getAttribute("aria-expanded")).toBe("false");
  // A legacy "verified" row (label and all) is drawn as the illustration RW5a's rules make it.
  expect(line.textContent).toContain(FIGURE_FRAME.illustration);
  expect(line.textContent).not.toContain("checked)");
  expect(document.querySelector("[data-figure-body]")).toBeNull();
  fireEvent.click(line);
  expect(line.getAttribute("aria-expanded")).toBe("true");
  expect(document.querySelector("[data-figure-body]")).not.toBeNull();
  expect(screen.getByText(FLAGSHIP.demonstrates)).toBeTruthy();
});

it("shows an illustration's own label, never the checked one (G23)", async () => {
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [figureView({
    verification: "illustrative", kind: "reconstructed",
    label: "AI-built illustration of an interpretation · not checked against the book" })] });
  render(<Harness spans={["p3"]} />);
  const line = await screen.findByRole("button", { name: /interactive version/ });
  expect(line.textContent).toContain("not checked against the book");
  expect(line.textContent).not.toContain("(checked)");
});

it("opens one figure at a time", async () => {
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [
    figureView(), figureView({ figureId: "fig_2", spanIds: ["p5"], anchorSpanId: "p5" })] });
  render(<Harness spans={["p3", "p5"]} />);
  const lines = await screen.findAllByRole("button", { name: /interactive version/ });
  fireEvent.click(lines[0]);
  fireEvent.click(lines[1]);
  expect(lines[0].getAttribute("aria-expanded")).toBe("false");
  expect(lines[1].getAttribute("aria-expanded")).toBe("true");
  expect(document.querySelectorAll("[data-figure-body]")).toHaveLength(1);
});

it("RW5d re-review F10: a figure placed under two paragraphs opens at one placement, and its prediction is that placement's", async () => {
  // A goal-only figure reused at p3 and p5: one figure id, two placements.
  const placed = (anchorSpanId: string) => figureView({ spanIds: [], anchorSpanId, goalText: "show how the mass moves" } as Partial<FigureViewDto>);
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [placed("p3"), placed("p5")] });
  api.readerFigurePredict.mockResolvedValue({
    predictionId: "fpr_1", figureId: "fig_1", extractionId: "ext_prob", predictionIndex: 0, learnerAnswer: "falls",
    matched: false, before: 0.3, after: 0.3, answer: "same", explanationText: null,
  } satisfies FigurePredictionResultDto);
  render(<Harness spans={["p3", "p5"]} />);
  const lines = await screen.findAllByRole("button", { name: /interactive version/ });
  expect(lines).toHaveLength(2);
  fireEvent.click(lines[0]);
  // Only the pressed placement opens.
  expect(lines[0].getAttribute("aria-expanded")).toBe("true");
  expect(lines[1].getAttribute("aria-expanded")).toBe("false");
  expect(document.querySelectorAll("[data-figure-body]")).toHaveLength(1);
  const atA = document.querySelector("[data-span='p3'] [data-figure-body]");
  expect(atA).not.toBeNull();
  fireEvent.click(screen.getByLabelText("it rises"));
  // Then the other placement: it opens alone, and what it shows selected is what it sends.
  fireEvent.click(lines[1]);
  expect(lines[0].getAttribute("aria-expanded")).toBe("false");
  expect(lines[1].getAttribute("aria-expanded")).toBe("true");
  expect(document.querySelector("[data-span='p5'] [data-figure-body]")).not.toBeNull();
  const falls = screen.getByLabelText("it falls") as HTMLInputElement;
  fireEvent.click(falls);
  expect(falls.checked).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: FIGURE_COPY.answer }));
  await waitFor(() => expect(api.readerFigurePredict).toHaveBeenCalledWith({ figureId: "fig_1", predictionIndex: 0, answer: "falls" }));
  // The result is the figure's, shared by both placements.
  await waitFor(() => expect(document.querySelector("[data-span='p5'] [data-figure-before-after]")).not.toBeNull());
  fireEvent.click(lines[0]);
  expect(document.querySelector("[data-span='p3'] [data-figure-before-after]")).not.toBeNull();
});

it("RW5d re-review F10: two mounted prediction controls for one figure never share a radio group", async () => {
  // The same figure open in two hosts at once (two controllers): each radio
  // group is its own, so choosing in one leaves the other's choice alone.
  render(<><Harness spans={["p3"]} /><Harness spans={["p3"]} /></>);
  const lines = await screen.findAllByRole("button", { name: /interactive version/ });
  fireEvent.click(lines[0]);
  fireEvent.click(lines[1]);
  const [rises] = screen.getAllByLabelText("it rises") as HTMLInputElement[];
  const [, falls] = screen.getAllByLabelText("it falls") as HTMLInputElement[];
  expect(rises.name).not.toBe(falls.name);
  fireEvent.click(rises);
  fireEvent.click(falls);
  expect(rises.checked).toBe(true);
  expect(falls.checked).toBe(true);
});

it("asks the prediction before the first change, then shows the readout before and after (Moment 9)", async () => {
  const result: FigurePredictionResultDto = {
    predictionId: "fpr_1", figureId: "fig_1", extractionId: "ext_prob", predictionIndex: 0, learnerAnswer: "rises",
    matched: false, before: 0.3, after: 0.3, answer: "same", explanationText: null,
  };
  api.readerFigurePredict.mockResolvedValue(result);
  api.readerFigureExplain.mockResolvedValue({ ...result, explanationText: "λ squeezes both sides toward 0, but p sets the split" });
  render(<Harness spans={["p3"]} />);
  fireEvent.click(await screen.findByRole("button", { name: /interactive version/ }));
  expect(screen.getByText(/Before you move anything:/)).toBeTruthy();
  const lambda = screen.getByLabelText("λ") as HTMLInputElement;
  expect(lambda.disabled).toBe(true); // nothing moves before the prediction
  fireEvent.click(screen.getByLabelText("it rises"));
  fireEvent.click(screen.getByRole("button", { name: FIGURE_COPY.answer }));
  await waitFor(() => expect(document.querySelector("[data-figure-before-after]")).not.toBeNull());
  expect(api.readerFigurePredict).toHaveBeenCalledWith({ figureId: "fig_1", predictionIndex: 0, answer: "rises" });
  expect(document.querySelector("[data-figure-before-after]")!.textContent).toBe("30.0% → 30.0%");
  expect(screen.getByText(/not what you predicted/)).toBeTruthy();
  expect((screen.getByLabelText("λ") as HTMLInputElement).disabled).toBe(false);
  expect((screen.getByLabelText("λ value") as HTMLInputElement).value).toBe("2"); // the change is applied
  expect(screen.getByText(/Never a grade/)).toBeTruthy(); // where this goes (UX §4.10)
  fireEvent.change(screen.getByLabelText(/what changed\? \(optional\)/), { target: { value: "λ squeezes both sides toward 0, but p sets the split" } });
  fireEvent.click(screen.getByRole("button", { name: FIGURE_COPY.save }));
  await waitFor(() => expect(api.readerFigureExplain).toHaveBeenCalledWith({
    predictionId: "fpr_1", text: "λ squeezes both sides toward 0, but p sets the split" }));
  expect(await screen.findByText(/› λ squeezes both sides/)).toBeTruthy();
});

it("lets the learner skip the prediction, and shows none while predictions are off", async () => {
  const { unmount } = render(<Harness spans={["p3"]} />);
  fireEvent.click(await screen.findByRole("button", { name: /interactive version/ }));
  fireEvent.click(screen.getByRole("button", { name: FIGURE_COPY.skip }));
  expect((screen.getByLabelText("λ") as HTMLInputElement).disabled).toBe(false);
  expect(api.readerFigurePredict).not.toHaveBeenCalled();
  unmount();
  render(<Harness spans={["p3"]} contract={{ ...CONTRACT, predictions: false }} />);
  fireEvent.click(await screen.findByRole("button", { name: /interactive version/ }));
  expect(screen.queryByText(/Before you move anything:/)).toBeNull();
});

it("plays only when pressed, through the same evaluation as the slider (G45)", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [figureView({ predictions: [] })] });
  render(<Harness spans={["p3"]} />);
  fireEvent.click(await screen.findByRole("button", { name: /interactive version/ }));
  const value = () => Number((screen.getByLabelText("λ value") as HTMLInputElement).value);
  const readout = () => document.querySelector('[data-figure-panel="readout"]')!.textContent;
  await act(async () => { vi.advanceTimersByTime(3000); });
  expect(value()).toBe(1); // nothing moved by itself
  fireEvent.click(screen.getByRole("button", { name: FIGURE_COPY.play }));
  await act(async () => { vi.advanceTimersByTime(150 * 12); });
  const lam = value();
  expect(lam).toBeGreaterThan(0.5);
  expect(lam).toBeLessThan(4);
  const compiled = compileSpec(FLAGSHIP);
  const expected = evaluateFigure(compiled, { lam }).panels[1];
  expect(expected.kind).toBe("readout");
  expect(readout()).toContain(formatValue((expected as { value: number | null }).value, "percent"));
  // Typing the same value into the slider's field gives the same readout.
  fireEvent.click(screen.getByRole("button", { name: FIGURE_COPY.stop }));
  fireEvent.change(screen.getByLabelText("λ value"), { target: { value: String(lam) } });
  expect(readout()).toContain(formatValue((expected as { value: number | null }).value, "percent"));
});

it("offers step buttons instead of play under reduced motion", async () => {
  const original = window.matchMedia;
  window.matchMedia = ((query: string) => ({ matches: query.includes("reduce"), media: query, addEventListener: () => undefined,
    removeEventListener: () => undefined, onchange: null, addListener: () => undefined, removeListener: () => undefined,
    dispatchEvent: () => false })) as unknown as typeof window.matchMedia;
  try {
    api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [figureView({ predictions: [] })] });
    render(<Harness spans={["p3"]} />);
    fireEvent.click(await screen.findByRole("button", { name: /interactive version/ }));
    expect(screen.queryByRole("button", { name: FIGURE_COPY.play })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: FIGURE_COPY.stepForward }));
    expect(Number((screen.getByLabelText("λ value") as HTMLInputElement).value)).toBeCloseTo(1 + 3.5 / 20, 6);
  } finally {
    window.matchMedia = original;
  }
});

it("gives every plot a values table (t)", async () => {
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [figureView({ predictions: [] })] });
  render(<Harness spans={["p3"]} />);
  fireEvent.click(await screen.findByRole("button", { name: /interactive version/ }));
  expect(screen.queryByRole("table", { name: "values as a table" })).toBeNull();
  fireEvent.keyDown(document.querySelector("[data-figure-body]")!, { key: "t" });
  const table = screen.getByRole("table", { name: "values as a table" });
  expect(table.textContent).toContain("P(X ≤ 0)");
  fireEvent.click(screen.getByRole("button", { name: FIGURE_COPY.table }));
  expect(screen.queryByRole("table", { name: "values as a table" })).toBeNull();
});

it("asks for a better version with the learner's note (not right?)", async () => {
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [figureView({ predictions: [] })] });
  api.readerFigureRevise.mockResolvedValue({ jobId: "ljob_1", kind: "figure_build", askId: null, state: "done",
    result: { reused: false, figure: figureView({ figureId: "fig_3", supersedesId: "fig_1", versions: 2, predictions: [] }) } });
  render(<Harness spans={["p3"]} />);
  fireEvent.click(await screen.findByRole("button", { name: /interactive version/ }));
  fireEvent.click(screen.getByRole("button", { name: FIGURE_COPY.notRight }));
  fireEvent.change(screen.getByLabelText(FIGURE_COPY.notRight), { target: { value: "the slider for λ should start at 0.1" } });
  fireEvent.click(screen.getByRole("button", { name: FIGURE_COPY.askBetter }));
  await waitFor(() => expect(api.readerFigureRevise).toHaveBeenCalledWith({ figureId: "fig_1", note: "the slider for λ should start at 0.1" }));
  await waitFor(() => expect(document.querySelector('[data-figure="fig_3"]')).not.toBeNull());
  expect(document.querySelector('[data-figure="fig_1"]')).toBeNull();
});

it("shows a failed build with try again, and an unsupported one as noted", async () => {
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [
    figureView({ verification: "failed", kind: null, specJson: null, predictions: [],
      label: "couldn't build a reliable version of this (integrates_to_one on 'f': integrates to 0.5, not 1)" }),
    figureView({ figureId: "fig_u", spanIds: ["p5"], anchorSpanId: "p5", verification: "unsupported", kind: null,
      specJson: null, predictions: [], unsupportedKind: "a 3-D surface", label: "can't draw this yet — needs a 3-D surface · noted" }),
  ] });
  api.readerFigureRequest.mockResolvedValue({ jobId: "ljob_2", kind: "figure_build", askId: null, state: "pending", result: null });
  render(<Harness spans={["p3", "p5"]} />);
  expect(await screen.findByText(FIGURE_FRAME.failed)).toBeTruthy();
  expect(screen.getByText(FIGURE_FRAME.unsupported)).toBeTruthy();
  expect(screen.queryAllByRole("button", { name: /interactive version/ })).toHaveLength(0);
  fireEvent.click(screen.getByRole("button", { name: FIGURE_COPY.tryAgain }));
  expect(api.readerFigureRequest).toHaveBeenCalledWith({ extractionId: "ext_prob", spanIds: ["p3"], region: null });
  expect(await screen.findByText(FIGURE_COPY.pending)).toBeTruthy();
});

it("builds in the background under its passage and moves no focus when it lands (W12, G54)", async () => {
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [] });
  let finish: (value: unknown) => void = () => undefined;
  api.readerFigureRequest.mockResolvedValue({ jobId: "ljob_3", kind: "figure_build", askId: null, state: "pending", result: null });
  api.readerFigureJob.mockImplementation(() => new Promise((resolve) => { finish = resolve; }));
  vi.useFakeTimers({ shouldAdvanceTime: true });
  render(<Harness spans={["p2"]} />);
  fireEvent.click(screen.getByRole("button", { name: "make p2 explorable" }));
  const elsewhere = screen.getByRole("button", { name: "elsewhere" });
  elsewhere.focus();
  expect(await screen.findByText(FIGURE_COPY.pending)).toBeTruthy();
  await act(async () => { vi.advanceTimersByTime(1600); });
  await act(async () => {
    finish({ jobId: "ljob_3", kind: "figure_build", askId: null, state: "done",
      result: { reused: false, figure: figureView({ figureId: "fig_new", spanIds: ["p2"], anchorSpanId: "p2" }) } });
  });
  await waitFor(() => expect(document.querySelector('[data-figure="fig_new"]')).not.toBeNull());
  expect(document.activeElement).toBe(elsewhere);
  expect(screen.queryByText(FIGURE_COPY.pending)).toBeNull();
});

it("a refused build keeps the request and says why", async () => {
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [] });
  api.readerFigureRequest.mockRejectedValue({ code: "capped", message: "Today's figure budget ($1.00) is used. Figures already built still open.", retryable: true });
  render(<Harness spans={["p2"]} />);
  fireEvent.click(screen.getByRole("button", { name: "make p2 explorable" }));
  expect(await screen.findByText(/Today's figure budget/)).toBeTruthy();
  expect(screen.getByRole("button", { name: FIGURE_COPY.tryAgain })).toBeTruthy();
});

it("is inert while the contract has no figures (no RPC, nothing drawn)", async () => {
  function Off() {
    const ctl = useFigures({ extractionId: "ext_prob", contract: null });
    return <FiguresUnder ctl={ctl} spanId="p3" />;
  }
  const { container } = render(<Off />);
  await act(async () => { await Promise.resolve(); });
  expect(api.readerFigures).not.toHaveBeenCalled();
  expect(container.innerHTML).toBe("");
});

it("never lets model text into the badge slot: the frame is code-owned (final round, High 1)", async () => {
  // Every model-authored field says "checked"; so do the server's label and an unknown check key.
  const claim = "matches the book's equation (checked)";
  const spec = JSON.parse(JSON.stringify(FLAGSHIP)) as FigureSpec & { panels: Array<Record<string, unknown>> };
  spec.demonstrates = claim;
  spec.panels.push({ kind: "readout", label: claim, expr: "1", format: "number" });
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [
    figureView({ verification: "illustrative", label: claim, reason: claim, specJson: JSON.stringify(spec),
      demonstrates: claim, propertyChecks: ["values_finite", "integrates_to_one", claim] }),
    figureView({ figureId: "fig_f", spanIds: ["p5"], anchorSpanId: "p5", verification: "failed", kind: null,
      specJson: null, predictions: [], label: claim, reason: claim }),
    figureView({ figureId: "fig_u", spanIds: ["p6"], anchorSpanId: "p6", verification: "unsupported", kind: null,
      specJson: null, predictions: [], label: claim, unsupportedKind: claim }),
  ] });
  render(<Harness spans={["p3", "p5", "p6"]} />);
  const line = await screen.findByRole("button", { name: /interactive version/ });
  fireEvent.click(line);
  await waitFor(() => expect(document.querySelectorAll("[data-figure-badge]")).toHaveLength(3));
  const badges = [...document.querySelectorAll("[data-figure-badge]")].map((node) => node.textContent);
  expect(badges).toEqual([FIGURE_FRAME.illustration, FIGURE_FRAME.failed, FIGURE_FRAME.unsupported]);
  for (const node of document.querySelectorAll("[data-figure-badge], [data-figure-checks]")) {
    expect(node.textContent).not.toContain("checked)");
    expect(node.textContent).not.toContain("matches the book");
  }
  expect(document.querySelector("[data-figure-checks]")?.textContent).toBe(
    `${FIGURE_FRAME.checksLead} ${PROPERTY_CHECK_COPY.values_finite}; ${PROPERTY_CHECK_COPY.integrates_to_one}`);
  // The model's words still render, inside the frame (the claim surface is ruled Low there).
  expect(screen.getAllByText(claim).length).toBeGreaterThan(0);
});
