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
import { SKETCH_COPY, SKETCH_FRAME, sketchBadge, sketchCheckLines } from "./SketchFigure";
import { hostRunner, SketchRunnerContext, WATCHDOG_MS, type SketchRunner, type SketchRunnerFactory } from "./sketchRunner";
import { newHost } from "./engineForTests";
import type { SketchEngineHost } from "./sketchEngine";

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
const SKETCH = {
  engineSha256: parity.engine_sha256, seed: 1, settings: 27, unnamedElements: 0, notCovered: ["walkers"],
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
  expect(rows[0].textContent).toContain("1 points");
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
