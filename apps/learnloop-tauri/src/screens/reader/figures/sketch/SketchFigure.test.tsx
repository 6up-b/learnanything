// Reader RW5d P2: the sketch on the page (spec_reader_show_me_figures_v1 §6.6, §9.1, §9.3).
//
// The real engine runs in-process (the app runs it in a Worker): the badge
// and check lines are code-owned; the renderer draws SVG primitives and text
// nodes only; handles set their parameters; play drives the clock; a seeded
// sketch draws a new sample; the values table shows the declared probes; an
// error says so and prefills "not right?"; a call past the watchdog pauses.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeAll, beforeEach, expect, it, vi } from "vitest";
import type { FigureViewDto } from "../../../../api/dto";
import parity from "./sketchParityCorpus.json";
import { FiguresUnder } from "../FigureInline";
import { useFigures, type FiguresContract } from "../useFigures";
import { SKETCH_COPY, SKETCH_FRAME, TABLE_PAGE, predictionTarget, sketchBadge, sketchCheckLines } from "./SketchFigure";
import { FIGURE_COPY } from "../FigureInline";
import { formatValue } from "../FigurePanels";
import { hostRunner, SketchRunnerContext, WATCHDOG_MS, type SketchRunner, type SketchRunnerFactory } from "./sketchRunner";
import { newHost } from "./engineForTests";
import type { SketchEngineHost } from "./sketchEngine";
import { resetWithdrawnChecks } from "./checksWithdrawn";

const api = vi.hoisted(() => ({
  readerFigures: vi.fn(), readerFigureRequest: vi.fn(), readerFigureJob: vi.fn(), readerFigureJobCancel: vi.fn(),
  readerFigureRevise: vi.fn(), readerFigurePredict: vi.fn(), readerFigureExplain: vi.fn(), readerLogActivity: vi.fn(),
}));
vi.mock("../../../../api/client", () => ({ api }));

const CONTRACT: FiguresContract = { predictions: true, region: true, revisions: true, sketch: true };
const code = (name: string) => parity.cases.find((item) => item.name === name)!.code;

const WALK = {
  program_version: "sketch-v1", demonstrates: "a random walk's spread grows like the square root of n",
  parameters: [{ name: "walkers", label: "walkers", min: 100, max: 400, step: 100, default: 200 }],
  clock: { dt: 1, t_max: 100 }, seeded: true, code: code("random walk"),
  probes: [{ name: "envelope", label: "the square-root envelope", shape: "pairs" }, { name: "msd", label: "mean squared position", shape: "scalar" },
    { name: "count", label: "walkers", shape: "scalar" }, { name: "sqvar", label: "variance of the squared positions", shape: "scalar" }],
};
const SPIRAL = {
  program_version: "sketch-v1", demonstrates: "complex eigenvalues make trajectories spiral",
  parameters: [{ name: "a", label: "real part a", min: -0.5, max: 0.5, step: 0.05, default: -0.2 },
    { name: "b", label: "imaginary part b", min: 0.2, max: 1.5, step: 0.05, default: 0.8 }],
  seeded: false, code: code("spiral"),
  probes: [{ name: "path", label: "the trajectory from (1, 0)", shape: "pairs" }, { name: "radius", label: "|a + bi|", shape: "scalar" }],
};
// The verifier's schedule and digests for the random walk (the parity corpus's verified entry, made by the
// sidecar): the page compares its reads with them (fix round 4).
const WALK_VERIFIED = (parity as unknown as { verified: Array<{ name: string; sketch: { readSteps: number[]; tested: Array<{ values: number[]; steps: number[]; digests: string[] }> } }> })
  .verified.find((item) => item.name === "random walk")!.sketch;
const SKETCH = {
  engineSha256: parity.engine_sha256, seed: 1, settings: 27, unnamedElements: 0, notCovered: ["walkers"],
  readSteps: WALK_VERIFIED.readSteps, tested: WALK_VERIFIED.tested,
  checks: [
    { claim: 0, kind: "equals" as const, probe: "envelope", elements: ["envelope"], statement: "sqrt(x)", settings: 27 },
    { claim: 1, kind: "distribution" as const, probe: "msd", elements: [], statement: "t", settings: 27 },
  ],
};

function sketchView(program: object, overrides: Partial<FigureViewDto> = {}): FigureViewDto {
  return {
    figureId: "fig_s", extractionId: "ext_prob", spanIds: ["p3"], anchorSpanId: "p3", region: null, origin: "selection",
    verification: "illustrative", kind: "illustrative", label: SKETCH_FRAME.badge, reason: null, unsupportedKind: null,
    supersedesId: null, revisionNote: null, versions: 1, createdAt: "2026-10-31T00:00:00", specJson: JSON.stringify(program),
    demonstrates: (program as { demonstrates: string }).demonstrates, assumptions: [], predictions: [], propertyChecks: [],
    tier: "sketch", sketch: SKETCH, grounding: "anchor", ...overrides,
  };
}

let host: SketchEngineHost;
let factory: SketchRunnerFactory;

function Harness({ runners = factory }: { runners?: SketchRunnerFactory }) {
  const ctl = useFigures({ extractionId: "ext_prob", contract: CONTRACT });
  return (
    <SketchRunnerContext.Provider value={runners}>
      <div data-span="p3"><FiguresUnder ctl={ctl} spanId="p3" /></div>
    </SketchRunnerContext.Provider>
  );
}

async function open(view: FigureViewDto, runners?: SketchRunnerFactory) {
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [view] });
  render(<Harness runners={runners} />);
  fireEvent.click(await screen.findByRole("button", { name: /interactive version/ }));
}

beforeAll(async () => {
  host = await newHost();
  // jsdom has no PointerEvent: a MouseEvent with a pointerId stands in, so clientX/clientY arrive.
  if (typeof window.PointerEvent === "undefined") {
    class PointerEventShim extends MouseEvent {
      pointerId: number;
      constructor(type: string, init: MouseEventInit & { pointerId?: number } = {}) {
        super(type, init);
        this.pointerId = init.pointerId ?? 1;
      }
    }
    (window as unknown as { PointerEvent: unknown }).PointerEvent = PointerEventShim;
  }
});
beforeEach(() => {
  vi.resetAllMocks();
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerFigureRevise.mockResolvedValue({ jobId: "job", state: "pending" });
  // A fresh engine per runner, as a Worker would be.
  factory = () => {
    let created: SketchRunner | null = null;
    const ready = newHost().then((fresh) => (created = hostRunner(fresh)));
    const via = <T,>(call: (runner: SketchRunner) => Promise<T>) => ready.then(call);
    return {
      load: (text) => via((runner) => runner.load(text)), init: (p, s) => via((runner) => runner.init(p, s)),
      step: (p, dt, i, c) => via((runner) => runner.step(p, dt, i, c)), read: (p, i) => via((runner) => runner.read(p, i)),
      dispose: () => created?.dispose(),
    };
  };
});
afterEach(() => {
  cleanup();
  resetWithdrawnChecks();
  vi.useRealTimers();
});

it("words the badge and the check lines from closed fields only", () => {
  expect(sketchBadge({ grounding: "anchor", sketch: SKETCH })).toBe("AI-written simulation · sandboxed · not checked against the book");
  expect(sketchBadge({ grounding: "anchor", sketch: { ...SKETCH, checks: [] } })).toBe(SKETCH_FRAME.unchecked);
  expect(sketchBadge({ grounding: "none", sketch: SKETCH })).toBe(SKETCH_FRAME.notFromBooks);
  expect(sketchCheckLines(SKETCH)).toEqual([
    "the drawn ‘envelope’ is sqrt(x) (AI-stated) at 27 tested settings",
    "the value ‘msd’ agrees with t (AI-stated) within sampling error at 27 tested settings",
    "not covered: ‘walkers’ (drawn, not checked)",
  ]);
});

it("collapses to one line with the sketch badge and opens to the drawn scene and its checks", async () => {
  await open(sketchView(WALK));
  const line = screen.getByRole("button", { name: /interactive version/ });
  expect(line.textContent).toContain(SKETCH_FRAME.badge);
  await waitFor(() => expect(document.querySelector('[data-sketch-element="envelope"]')).not.toBeNull());
  expect(document.querySelector('[data-sketch-element="walkers"]')?.querySelectorAll("circle").length).toBe(200);
  const checks = Array.from(document.querySelectorAll("[data-sketch-check-line]")).map((node) => node.textContent);
  expect(checks[0]).toContain("‘envelope’ is sqrt(x)");
  expect(screen.getByText(SKETCH_FRAME.checksLead)).toBeTruthy();
  expect(document.querySelector("[data-sketch-new-sample]")).not.toBeNull();
  // Nothing it started took focus.
  expect(document.querySelector("[data-sketch-body]")!.contains(document.activeElement)).toBe(false);
});

it("plays the clock forward only when pressed", async () => {
  await open(sketchView(WALK));
  await waitFor(() => expect(document.querySelector("[data-sketch-time]")?.textContent).toContain("t = 0 / 100"));
  await new Promise((resolve) => setTimeout(resolve, 150));
  expect(document.querySelector("[data-sketch-time]")?.textContent).toContain("t = 0 / 100");
  fireEvent.click(document.querySelector("[data-sketch-play]")!);
  await waitFor(() => expect(document.querySelector("[data-sketch-time]")?.textContent).not.toContain("t = 0 /"), { timeout: 2000 });
  fireEvent.click(document.querySelector("[data-sketch-play]")!);
  expect(document.querySelector("[data-sketch-play]")?.textContent).toBe(SKETCH_COPY.play);
});

it("draws a new sample with another seed", async () => {
  await open(sketchView(WALK));
  await waitFor(() => expect(document.querySelector("[data-sketch-play]")).not.toBeNull());
  fireEvent.click(document.querySelector("[data-sketch-play]")!);
  await waitFor(() => expect(document.querySelector("[data-sketch-time]")?.textContent).not.toContain("t = 0 /"), { timeout: 2000 });
  fireEvent.click(document.querySelector("[data-sketch-play]")!);
  const before = document.querySelector('[data-sketch-element="walkers"]')!.innerHTML;
  fireEvent.click(document.querySelector("[data-sketch-new-sample]")!);
  await waitFor(() => expect(document.querySelector("[data-sketch-time]")?.textContent).toContain("t = 0 / 100"));
  // At t = 0 every walker is at 0 whatever the seed; play a little and compare.
  fireEvent.click(document.querySelector("[data-sketch-play]")!);
  await waitFor(() => expect(document.querySelector('[data-sketch-element="walkers"]')!.innerHTML).not.toBe(before), { timeout: 2000 });
});

it("shows the declared probes in the values table (t)", async () => {
  await open(sketchView(WALK));
  await waitFor(() => expect(document.querySelector('[data-sketch-element="envelope"]')).not.toBeNull());
  fireEvent.keyDown(document.querySelector("[data-sketch-body]")!, { key: "t" });
  const rows = Array.from(document.querySelectorAll("[data-sketch-probe]"));
  expect(rows.map((row) => row.getAttribute("data-sketch-probe"))).toEqual(["envelope", "msd", "count", "sqvar"]);
  expect(rows[2].textContent).toContain("walkers");
  expect(rows[2].textContent).toContain("200");
  expect(rows[0].textContent).toContain("points 1–1 of 1");
});

it("moves its bound parameters when a handle is dragged", async () => {
  await open(sketchView(SPIRAL, { sketch: { ...SKETCH, checks: [], notCovered: ["trajectory"], unnamedElements: 1 } }));
  const handle = await waitFor(() => {
    const found = document.querySelector('[data-sketch-handle="ab"]');
    expect(found).not.toBeNull();
    return found!;
  });
  const svg = document.querySelector("[data-sketch-scene]")!;
  // jsdom has no layout: the scene's own units stand in for the pointer's (a = 0.3 at x 355.1, b = 1.0 at y 75.5).
  fireEvent.pointerDown(handle, { pointerId: 1, clientX: 0, clientY: 0 });
  fireEvent.pointerMove(svg, { pointerId: 1, clientX: 355.1, clientY: 75.5 });
  fireEvent.pointerUp(svg, { pointerId: 1 });
  await waitFor(() => expect((screen.getByLabelText("real part a value") as HTMLInputElement).value).toBe("0.3"));
  expect((screen.getByLabelText("imaginary part b value") as HTMLInputElement).value).toBe("1");
});

it("draws text as text, never as markup", async () => {
  const program = { ...SPIRAL, code: SPIRAL.code.replace('text: "a ± bi"', 'text: "<img src=x onerror=alert(1)>"') };
  await open(sketchView(program));
  await waitFor(() => expect(document.querySelector("[data-sketch-text]")).not.toBeNull());
  expect(document.querySelector("[data-sketch-text]")!.textContent).toBe("<img src=x onerror=alert(1)>");
  expect(document.querySelector("img")).toBeNull();
});

it("says when the simulation fails at these settings and prefills not right? with code's words", async () => {
  const program = { ...SPIRAL, code: SPIRAL.code.replace("function init(p, seed) { return {}; }", "function init(p, seed) { if (p.a > 0.2) throw new Error('blew up'); return {}; }") };
  await open(sketchView(program));
  await waitFor(() => expect(document.querySelector('[data-sketch-element="trajectory"]')).not.toBeNull());
  fireEvent.change(screen.getByLabelText("real part a value"), { target: { value: "0.4" } });
  await waitFor(() => expect(document.querySelector("[data-sketch-error]")).not.toBeNull());
  expect(document.querySelector("[data-sketch-error]")!.getAttribute("data-sketch-error")).toBe("error");
  fireEvent.click(document.querySelector("[data-sketch-error-not-right]")!);
  const note = document.querySelector("[data-sketch-note]") as HTMLInputElement;
  expect(note.value).toContain("this simulation hit an error at these settings: a=0.4, b=0.8");
  expect(note.value).toContain("blew up");
});

it("refuses to draw a scene the validator rejects", async () => {
  const program = { ...SPIRAL, code: SPIRAL.code.replace("viewport: {x: [-2, 2], y: [-2, 2]}", "viewport: {x: [-2, 0/0], y: [-2, 2]}") };
  await open(sketchView(program));
  await waitFor(() => expect(document.querySelector("[data-sketch-error]")).not.toBeNull());
  expect(document.querySelector("[data-sketch-error]")!.getAttribute("data-sketch-error")).toBe("scene");
  expect(document.querySelector("[data-sketch-scene]")).toBeNull();
});

it("pauses a sketch whose call outlives the watchdog, and resumes on request", async () => {
  let made = 0;
  const stuck: SketchRunnerFactory = () => {
    made += 1;
    const first = made === 1;
    const real = hostRunner(host);
    return {
      load: (text) => real.load(text), init: (p, s) => real.init(p, s), step: (p, dt, i, c) => real.step(p, dt, i, c),
      read: (p, i) => (first ? new Promise(() => undefined) : real.read(p, i)), dispose: () => undefined,
    };
  };
  await open(sketchView(SPIRAL), stuck);
  await waitFor(() => expect(document.querySelector("[data-sketch-paused]")).not.toBeNull(), { timeout: WATCHDOG_MS + 1500 });
  expect(screen.getByText(SKETCH_COPY.paused)).toBeTruthy();
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: SKETCH_COPY.resume }));
  });
  await waitFor(() => expect(document.querySelector('[data-sketch-element="trajectory"]')).not.toBeNull());
  expect(made).toBe(2);
});

it("explains how it runs on demand, without jargon in the badge", async () => {
  await open(sketchView(SPIRAL));
  expect(document.querySelector("[data-sketch-how]")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: SKETCH_COPY.howItRunsLink }));
  expect(document.querySelector("[data-sketch-how]")!.textContent).toContain("can't see your files");
  expect(screen.getByRole("button", { name: /interactive version/ }).textContent).not.toMatch(/wasm|QuickJS|sandbox escape/i);
});

// ---------------------------------------------------------------------------
// Codex review F3: a check that speaks for one attribute says which
// ---------------------------------------------------------------------------

it("words a partial check as the attribute it checked", () => {
  const lines = sketchCheckLines({
    ...SKETCH, notCovered: [], checks: [
      { claim: 0, kind: "invariant", probe: "cells", elements: [], partial: [{ element: "grid", attribute: "values" }], statement: "never negative", settings: 9 },
      { claim: 1, kind: "invariant", probe: "v", elements: [], partial: [{ element: "line", attribute: "y" }], statement: "bounded", settings: 9 },
      { claim: 2, kind: "equals", probe: "r", elements: [], partial: [{ element: "dot", attribute: "r" }], statement: "sqrt(t)", settings: 9 },
      { claim: 3, kind: "equals", probe: "v", elements: [], partial: [], statement: "x", settings: 9 },
    ],
  });
  expect(lines).toEqual([
    "the cell values of the drawn ‘grid’ are never negative at 9 tested settings",
    "the y values of the drawn ‘line’ are bounded at 9 tested settings",
    "the radius of the drawn ‘dot’ is sqrt(t) (AI-stated) at 9 tested settings",
    "the value ‘v’ is x (AI-stated) at 9 tested settings",
  ]);
});

// ---------------------------------------------------------------------------
// Codex review F4: delayed Worker responses never mix runs
// ---------------------------------------------------------------------------

/** The in-process engine with the Worker's ordering (each call runs when
 *  sent), but step responses held back until released, as a slow Worker's
 *  would be. Every call is logged with the walkers it was sent. */
function delayedSteps(log: string[], held: Array<() => void>): SketchRunnerFactory {
  return () => {
    let created: SketchRunner | null = null;
    const ready = newHost().then((fresh) => (created = hostRunner(fresh)));
    const via = <T,>(call: (runner: SketchRunner) => Promise<T>) => ready.then(call);
    return {
      load: (text) => via((runner) => runner.load(text)),
      init: (p, s) => via((runner) => { log.push(`init ${p.walkers}`); return runner.init(p, s); }),
      step: (p, dt, i, c) => via((runner) => {
        log.push(`step ${p.walkers}`);
        const done = runner.step(p, dt, i, c);
        return new Promise<void>((resolve, reject) => { held.push(() => { done.then(resolve, reject); }); });
      }),
      read: (p, i) => via((runner) => { log.push(`read ${p.walkers} ${i}`); return runner.read(p, i); }),
      dispose: () => created?.dispose(),
    };
  };
}

function time() {
  return document.querySelector("[data-sketch-time]")?.textContent ?? "";
}

async function settleAfterRelease(held: Array<() => void>) {
  await act(async () => {
    while (held.length) held.shift()!();
    await new Promise((resolve) => setTimeout(resolve, 150));
  });
}

it("never draws a superseded frame when a slider moves while a step is in flight", async () => {
  const log: string[] = [];
  const held: Array<() => void> = [];
  await open(sketchView(WALK), delayedSteps(log, held));
  await waitFor(() => expect(time()).toContain("t = 0 / 100"));
  fireEvent.click(document.querySelector("[data-sketch-play]")!);
  await waitFor(() => expect(held.length).toBe(1));  // a step(200) sent, its answer held
  fireEvent.change(screen.getByLabelText("walkers value"), { target: { value: "400" } });
  await settleAfterRelease(held);
  await waitFor(() => expect(document.querySelector('[data-sketch-element="walkers"]')?.querySelectorAll("circle").length).toBe(400));
  expect(time()).toContain("t = 0 / 100");  // the new run's init, not the old frame's step
  const init400 = log.indexOf("init 400");
  expect(init400).toBeGreaterThan(log.indexOf("step 200"));  // queued behind the call in flight
  expect(log.slice(init400).some((entry) => entry.startsWith("read 200"))).toBe(false);
  expect(log.slice(init400).some((entry) => entry.startsWith("step"))).toBe(false);
});

it("never draws a superseded frame when a new sample is drawn while a step is in flight", async () => {
  const log: string[] = [];
  const held: Array<() => void> = [];
  await open(sketchView(WALK), delayedSteps(log, held));
  await waitFor(() => expect(time()).toContain("t = 0 / 100"));
  fireEvent.click(document.querySelector("[data-sketch-play]")!);
  await waitFor(() => expect(held.length).toBe(1));
  fireEvent.click(document.querySelector("[data-sketch-new-sample]")!);
  await settleAfterRelease(held);
  await waitFor(() => expect(log.filter((entry) => entry === "init 200").length).toBe(2));
  expect(time()).toContain("t = 0 / 100");
  const second = log.lastIndexOf("init 200");
  expect(log.slice(second)).toEqual(["init 200", "read 200 0"]);
});

// ---------------------------------------------------------------------------
// Codex review F5: a prediction plays to exactly the step it was graded at
// ---------------------------------------------------------------------------

const AT_FIVE = { ...WALK, predictions: [{ prompt: "Run to n = 5: does the spread rise?", change: { run_to: 5 }, observe: { kind: "direction", probe: "msd" } }] };
const MORE_WALKERS = { ...WALK, predictions: [{ prompt: "With 400 walkers, does the spread change?", change: { walkers: 400 }, observe: { kind: "direction", probe: "msd" } }] };

function predicted(program: object, targetStep?: number): FigureViewDto {
  return sketchView(program, {
    predictions: [{ index: 0, prompt: "?", kind: "direction", answered: null, targetStep,
      choices: [{ value: "rises", label: "rises" }, { value: "falls", label: "falls" }, { value: "same", label: "same" }] }],
  });
}

async function answer() {
  api.readerFigurePredict.mockResolvedValue({ predictionId: "fp_1", figureId: "fig_s", extractionId: "ext_prob", predictionIndex: 0,
    learnerAnswer: "rises", matched: true, before: 0, after: 5, answer: "rises", explanationText: null });
  fireEvent.click(screen.getByLabelText("rises"));
  fireEvent.click(screen.getByRole("button", { name: FIGURE_COPY.answer }));
}

it("plays a run_to prediction to its graded step and stops there", async () => {
  // F5's scenario: 2,000 steps play 20 per tick; the answer was graded at step 5.
  await open(predicted({ ...AT_FIVE, clock: { dt: 1, t_max: 2000 } }, 5));
  await waitFor(() => expect(time()).toContain("t = 0 / 2000"));
  await answer();
  await waitFor(() => expect(time()).toContain("t = 5 / 2000"), { timeout: 3000 });
  await new Promise((resolve) => setTimeout(resolve, 300));
  expect(time()).toContain("t = 5 / 2000");  // not the play tick's 20 steps
  expect(document.querySelector("[data-sketch-play]")?.textContent).toBe(SKETCH_COPY.play);
});

it("plays a parameter-change prediction with its change to t_max, where it was graded", async () => {
  // 100 play ticks of 60 ms: the whole run, as the verifier compared it.
  await open(predicted(MORE_WALKERS, 100));
  await waitFor(() => expect(time()).toContain("t = 0 / 100"));
  await answer();
  await waitFor(() => expect(time()).toContain("t = 100 / 100"), { timeout: 12000 });
  expect((screen.getByLabelText("walkers value") as HTMLInputElement).value).toBe("400");
  expect(document.querySelector('[data-sketch-element="walkers"]')?.querySelectorAll("circle").length).toBe(400);
}, 15000);

it("goes straight to the graded step under reduced motion, with no animation", async () => {
  const original = window.matchMedia;
  window.matchMedia = ((query: string) => ({ matches: query.includes("reduce"), media: query, addEventListener: () => undefined,
    removeEventListener: () => undefined, onchange: null, addListener: () => undefined, removeListener: () => undefined,
    dispatchEvent: () => false })) as unknown as typeof window.matchMedia;
  const intervals = vi.spyOn(globalThis, "setInterval");
  try {
    await open(predicted(AT_FIVE, 5));
    await waitFor(() => expect(time()).toContain("t = 0 / 100"));
    intervals.mockClear();
    await answer();
    await waitFor(() => expect(time()).toContain("t = 5 / 100"));
    expect(intervals.mock.calls.filter(([, ms]) => ms === 60)).toEqual([]);  // no play interval started
    expect(document.querySelector("[data-sketch-play]")).toBeNull();
  } finally {
    intervals.mockRestore();
    window.matchMedia = original;
  }
});

it("computes the graded step like the verifier when the view predates it", () => {
  const program = AT_FIVE as unknown as Parameters<typeof predictionTarget>[0];
  expect(predictionTarget(program, { index: 0 })).toBe(5);
  expect(predictionTarget(MORE_WALKERS as unknown as Parameters<typeof predictionTarget>[0], { index: 0 })).toBe(100);
  expect(predictionTarget(program, { index: 0, targetStep: 7 })).toBe(7);
});

// ---------------------------------------------------------------------------
// Codex review F6: the values table has every declared value
// ---------------------------------------------------------------------------

const LONG = {
  program_version: "sketch-v1", demonstrates: "many values",
  parameters: [{ name: "k", label: "offset", min: 0, max: 1, step: 0.5, default: 0.5 }], seeded: false,
  code: "function init(p, seed) { return {}; }\n"
    + "function probes(s, p) { var v = [], q = []; for (var i = 0; i < 120; i++) { v.push(i * 10 + p.k); q.push([i, i * i]); } return {v: v, path: q, k: p.k}; }\n"
    + "function view(s, p) { return {viewport: {x: [0, 1], y: [0, 1]}, elements: []}; }",
  probes: [{ name: "v", label: "the series", shape: "series" }, { name: "path", label: "the path", shape: "pairs" },
    { name: "k", label: "the offset", shape: "scalar" }],
};

it("lists every entry of a series and both coordinates of every point, a page at a time", async () => {
  await open(sketchView(LONG, { sketch: { ...SKETCH, checks: [], notCovered: [] } }));
  await waitFor(() => expect(document.querySelector("[data-sketch-scene]")).not.toBeNull());
  fireEvent.click(screen.getByRole("button", { name: SKETCH_COPY.table }));
  const entries = (name: string) => Array.from(document.querySelectorAll(`[data-sketch-entries="${name}"] [data-sketch-entry]`));
  expect(entries("v").length).toBe(TABLE_PAGE);
  expect(document.querySelector('[data-sketch-entries="v"] [data-sketch-entry="49"]')!.textContent).toContain(formatValue(490.5));
  expect(document.querySelector('[data-sketch-entries="v"]')!.textContent).toContain("values 1–50 of 120");
  fireEvent.click(document.querySelector('[data-sketch-page-next="v"]')!);
  expect(document.querySelector('[data-sketch-entries="v"] [data-sketch-entry="75"]')!.textContent).toContain(formatValue(750.5));
  fireEvent.click(document.querySelector('[data-sketch-page-next="v"]')!);
  expect(entries("v").map((row) => row.getAttribute("data-sketch-entry"))).toEqual(Array.from({ length: 20 }, (_, i) => String(100 + i)));
  fireEvent.click(document.querySelector('[data-sketch-page-next="path"]')!);
  fireEvent.click(document.querySelector('[data-sketch-page-next="path"]')!);
  const last = document.querySelector('[data-sketch-entries="path"] [data-sketch-entry="119"]')!;
  const cells = Array.from(last.querySelectorAll("td")).map((cell) => cell.textContent);
  expect(cells).toEqual(["119", formatValue(119), formatValue(14161)]);
  expect(document.querySelector('[data-sketch-probe="k"]')!.textContent).toContain(formatValue(0.5));
});
