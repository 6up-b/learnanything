// Reader RW5d P2, fix round 4: the independent sandbox review (gpt-6-astra) through
// the desktop, with the committed engine in-process (the app runs it in a Worker).
//
// Finding 1: a run on the page is "a freshly loaded program, init, then the
// read schedule", the shape verification read; the desktop computes the
// digest of every scheduled read and compares it with the verifier's for the
// states it tested, and on any difference withdraws the code-owned checks
// (the illustration label, never "checked by LearnLoop"). Finding 2: a
// prediction plays exactly the value it was graded at.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { FigureSketchDto, FigureViewDto } from "../../../../api/dto";
import parity from "./sketchParityCorpus.json";
import hostileText from "./sketchHostileCorpus.json?raw";
import { FIGURE_COPY, FiguresUnder } from "../FigureInline";
import { useFigures, type FiguresContract } from "../useFigures";
import { SKETCH_FRAME } from "./SketchFigure";
import { resetWithdrawnChecks } from "./checksWithdrawn";
import { hostRunner, SketchRunnerContext, type SketchRunner, type SketchRunnerFactory } from "./sketchRunner";
import { newHost } from "./engineForTests";
import { readSchedule, type SketchProgram } from "./sketchScene";
import { canonicalJson, PLAY_TICKS, sceneDigest } from "./sketchEngine";

const api = vi.hoisted(() => ({
  readerFigures: vi.fn(), readerFigureRequest: vi.fn(), readerFigureJob: vi.fn(), readerFigureJobCancel: vi.fn(),
  readerFigureRevise: vi.fn(), readerFigurePredict: vi.fn(), readerFigureExplain: vi.fn(), readerLogActivity: vi.fn(),
}));
vi.mock("../../../../api/client", () => ({ api }));

const CONTRACT: FiguresContract = { predictions: true, region: true, revisions: true, sketch: true };
const hostile = JSON.parse(hostileText) as { cases: Array<{ name: string; code: string }> };
const COUNTING_CODE = hostile.cases.find((item) => item.name === "counting its own starts: every init is a fresh start")!.code;
type Verified = { name: string; program: SketchProgram & { predictions?: unknown[] }; sketch: FigureSketchDto };
const verified = (parity as unknown as { verified: Verified[] }).verified;
const WALK = verified.find((item) => item.name === "random walk")!;
const MARKS = verified.find((item) => item.name === "marks when read")!;
const SIGNED_ZERO = verified.find((item) => item.name === "signed zero")!;

function sketchView(program: object, sketch: FigureSketchDto, overrides: Partial<FigureViewDto> = {}): FigureViewDto {
  return {
    figureId: "fig_review", extractionId: "ext_prob", spanIds: ["p3"], anchorSpanId: "p3", region: null, origin: "selection",
    verification: "illustrative", kind: "illustrative", label: SKETCH_FRAME.badge, reason: null, unsupportedKind: null,
    supersedesId: null, revisionNote: null, versions: 1, createdAt: "2026-10-31T00:00:00", specJson: JSON.stringify(program),
    demonstrates: (program as { demonstrates: string }).demonstrates, assumptions: [], predictions: [], propertyChecks: [],
    tier: "sketch", sketch, grounding: "anchor", ...overrides,
  };
}

type Read = { params: Record<string, number>; index: number; digest: string };

/** A fresh engine per runner, as a Worker would be; every init and read logged. */
function logging(reads: Read[], inits: Array<Record<string, number>>): SketchRunnerFactory {
  return () => {
    let created: SketchRunner | null = null;
    const ready = newHost().then((fresh) => (created = hostRunner(fresh)));
    const via = <T,>(call: (runner: SketchRunner) => Promise<T>) => ready.then(call);
    return {
      load: (text) => via((runner) => runner.load(text)),
      init: (p, s) => via((runner) => { inits.push({ ...p }); return runner.init(p, s); }),
      step: (p, dt, i, c) => via((runner) => runner.step(p, dt, i, c)),
      read: (p, i) => via(async (runner) => { const result = await runner.read(p, i); reads.push({ params: { ...p }, index: i, digest: result.digest }); return result; }),
      dispose: () => created?.dispose(),
    };
  };
}

function Harness({ runners }: { runners: SketchRunnerFactory }) {
  const ctl = useFigures({ extractionId: "ext_prob", contract: CONTRACT });
  return (
    <SketchRunnerContext.Provider value={runners}>
      <div data-span="p3"><FiguresUnder ctl={ctl} spanId="p3" /></div>
    </SketchRunnerContext.Provider>
  );
}

async function open(view: FigureViewDto, runners: SketchRunnerFactory) {
  api.readerFigures.mockResolvedValue({ extractionId: "ext_prob", figures: [view] });
  render(<Harness runners={runners} />);
  fireEvent.click(await screen.findByRole("button", { name: /interactive version/ }));
}

const badge = () => document.querySelector("[data-figure-badge]")?.textContent ?? "";
const checkLines = () => Array.from(document.querySelectorAll("[data-sketch-check-line]")).map((node) => node.textContent ?? "");
const time = () => document.querySelector("[data-sketch-time]")?.textContent ?? "";

beforeEach(() => {
  vi.resetAllMocks();
  resetWithdrawnChecks();
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
});
afterEach(() => {
  cleanup();
});

// ---------------------------------------------------------------------------
// Finding 1: runtime history
// ---------------------------------------------------------------------------

it("withdraws the reviewer's false check: a fresh start at the default draws radius 9, not the 1 the old verifier read", async () => {
  const program = {
    program_version: "sketch-v1", demonstrates: "a dot of radius one", seeded: false, code: COUNTING_CODE,
    parameters: [{ name: "a", label: "a", min: 0, max: 2, step: 1, default: 1 }],
    probes: [{ name: "radius", label: "radius", shape: "scalar" }],
  };
  // What the old verifier read at a = 1, the program's second start on one load (after a = 0): radius 1, starts 2. (Every
  // init now reloads the program, so that read is written out here: the same program's text with one start already counted.)
  const later = await newHost();
  later.load(COUNTING_CODE.replace("let starts = 0;", "let starts = 1;"));
  later.init({ a: 1 }, 1);
  const { sceneText, probesText } = later.readText({ a: 1 }, 0);
  expect(JSON.parse(probesText)).toEqual({ radius: 1, starts: 2 });
  const stale = sceneDigest(sceneText, probesText);
  const sketch: FigureSketchDto = {
    engineSha256: parity.engine_sha256, seed: 1, settings: 3, unnamedElements: 0, notCovered: [], readSteps: [0],
    checks: [{ claim: 0, kind: "equals", probe: "radius", elements: [], partial: [{ element: "dot", attribute: "r" }], statement: "1", settings: 3 }],
    tested: [{ values: [1], steps: [0], digests: [stale] }],
  };
  const reads: Read[] = [];
  await open(sketchView(program, sketch), logging(reads, []));
  await waitFor(() => expect(document.querySelector('[data-sketch-element="dot"]')).not.toBeNull());
  fireEvent.keyDown(document.querySelector("[data-sketch-body]")!, { key: "t" });
  expect(document.querySelector('[data-sketch-probe="radius"]')!.textContent).toContain("9");
  await waitFor(() => expect(document.querySelector("[data-sketch-checks-withdrawn]")).not.toBeNull());
  expect(checkLines().some((line) => line.includes("radius of the drawn"))).toBe(false);
  expect(screen.queryByText(SKETCH_FRAME.checksLead)).toBeNull();
  expect(badge()).toBe(SKETCH_FRAME.unchecked);
  expect(reads[0].digest).not.toBe(stale);
});

it("keeps the checks when every tested read on the page matches the verifier's, played to t_max at the defaults", async () => {
  const reads: Read[] = [];
  await open(sketchView(WALK.program, WALK.sketch), logging(reads, []));
  await waitFor(() => expect(time()).toContain("t = 0 / 100"));
  fireEvent.click(document.querySelector("[data-sketch-play]")!);
  await waitFor(() => expect(time()).toContain("t = 100 / 100"), { timeout: 12000 });
  const atDefaults = WALK.sketch.tested!.find((entry) => entry.values[0] === 200)!;
  for (const [position, step] of atDefaults.steps.entries()) {
    const read = reads.find((entry) => entry.index === step && entry.params.walkers === 200);
    expect(read?.digest, `step ${step}`).toBe(atDefaults.digests[position]);
  }
  // The read schedule, each step once, in order: the history verification read.
  expect(reads.map((entry) => entry.index)).toEqual(WALK.sketch.readSteps);
  expect(document.querySelector("[data-sketch-checks-withdrawn]")).toBeNull();
  expect(checkLines()[0]).toContain("‘envelope’ is sqrt(x)");
  expect(badge()).toBe(SKETCH_FRAME.badge);
}, 15000);

it("matches the verifier's digests again after repeated restarts", async () => {
  const reads: Read[] = [];
  await open(sketchView(WALK.program, WALK.sketch), logging(reads, []));
  await waitFor(() => expect(reads.length).toBe(1));
  for (const value of ["400", "200", "100", "200"]) {
    fireEvent.change(screen.getByLabelText("walkers value"), { target: { value } });
    await waitFor(() => expect(reads[reads.length - 1]?.params.walkers).toBe(Number(value)));
  }
  const tested = (walkers: number) => WALK.sketch.tested!.find((entry) => entry.values[0] === walkers)!.digests[0];
  for (const read of reads) expect(read.digest).toBe(tested(read.params.walkers));
  expect(reads.filter((read) => read.params.walkers === 200).length).toBe(3);
  expect(document.querySelector("[data-sketch-checks-withdrawn]")).toBeNull();
});

it("reads every scheduled step on the way to a prediction under reduced motion, so a state marked when read matches", async () => {
  const original = window.matchMedia;
  window.matchMedia = ((query: string) => ({ matches: query.includes("reduce"), media: query, addEventListener: () => undefined,
    removeEventListener: () => undefined, onchange: null, addListener: () => undefined, removeListener: () => undefined,
    dispatchEvent: () => false })) as unknown as typeof window.matchMedia;
  try {
    const reads: Read[] = [];
    const view = sketchView(MARKS.program, MARKS.sketch, {
      predictions: [{ index: 0, prompt: "?", kind: "direction", answered: null, targetStep: 50,
        choices: [{ value: "rises", label: "rises" }, { value: "falls", label: "falls" }, { value: "same", label: "same" }] }],
    });
    await open(view, logging(reads, []));
    await waitFor(() => expect(time()).toContain("t = 0 / 100"));
    api.readerFigurePredict.mockResolvedValue({ predictionId: "fp_1", figureId: "fig_review", extractionId: "ext_prob", predictionIndex: 0,
      learnerAnswer: "rises", matched: true, before: 0, after: 383, answer: "rises", explanationText: null });
    fireEvent.click(screen.getByLabelText("rises"));
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: FIGURE_COPY.answer })); });
    await waitFor(() => expect(time()).toContain("t = 50 / 100"));
    const second = reads.slice(reads.map((read) => read.index).lastIndexOf(0));
    expect(second.map((read) => read.index)).toEqual(MARKS.sketch.readSteps!.filter((step) => step <= 50));
    const entry = MARKS.sketch.tested![0];
    const at50 = second.find((read) => read.index === 50)!;
    expect(at50.digest).toBe(entry.digests[entry.steps.indexOf(50)]);
    fireEvent.keyDown(document.querySelector("[data-sketch-body]")!, { key: "t" });
    expect(document.querySelector('[data-sketch-probe="x"]')!.textContent).toContain("383");
    expect(document.querySelector("[data-sketch-checks-withdrawn]")).toBeNull();
  } finally {
    window.matchMedia = original;
  }
});

it("computes the verifier's read schedule from the program alone", () => {
  for (const entry of verified) expect(readSchedule(entry.program)).toEqual(entry.sketch.readSteps);
  const long = { ...WALK.program, clock: { dt: 1, t_max: 2000 }, predictions: [{ prompt: "?", change: { run_to: 5 }, observe: { kind: "direction", probe: "msd" } }] } as SketchProgram;
  const steps = readSchedule(long);
  expect(steps.slice(0, 4)).toEqual([0, 5, 20, 40]);
  expect(steps.filter((step) => step % 20 === 0).length).toBe(PLAY_TICKS + 1);
});

// ---------------------------------------------------------------------------
// Finding 2: a prediction plays the value it was graded at
// ---------------------------------------------------------------------------

it("plays a prediction's parameter change at exactly the graded value, never re-snapped", async () => {
  const program = {
    program_version: "sketch-v1", demonstrates: "a dot whose radius is a", seeded: false,
    code: "function init(p){return p.a} function view(s){return {viewport:{x:[-2,2],y:[-2,2]},elements:[{type:'circle',id:'dot',cx:0,cy:0,r:s}]}} function probes(s){return {radius:s}}",
    parameters: [{ name: "a", label: "a", min: 0, max: 1, step: 1, default: 0 }],
    probes: [{ name: "radius", label: "radius", shape: "scalar" }],
    predictions: [{ prompt: "?", change: { a: 0.4 }, observe: { kind: "direction", probe: "radius" } }],
  };
  const sketch: FigureSketchDto = { engineSha256: parity.engine_sha256, seed: 1, settings: 0, unnamedElements: 0, notCovered: ["dot"], checks: [], tested: [], readSteps: [0] };
  const inits: Array<Record<string, number>> = [];
  await open(sketchView(program, sketch, {
    predictions: [{ index: 0, prompt: "?", kind: "direction", answered: null, targetStep: 0,
      choices: [{ value: "rises", label: "rises" }, { value: "falls", label: "falls" }, { value: "same", label: "same" }] }],
  }), logging([], inits));
  await waitFor(() => expect(inits.length).toBe(1));
  api.readerFigurePredict.mockResolvedValue({ predictionId: "fp_1", figureId: "fig_review", extractionId: "ext_prob", predictionIndex: 0,
    learnerAnswer: "rises", matched: true, before: 0, after: 0.4, answer: "rises", explanationText: null });
  fireEvent.click(screen.getByLabelText("rises"));
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: FIGURE_COPY.answer })); });
  await waitFor(() => expect(inits.length).toBe(2));
  expect(inits[1]).toEqual({ a: 0.4 });
});

// ---------------------------------------------------------------------------
// Verify round 2 (Astra): signed zero, and the graded step as a tested state
// ---------------------------------------------------------------------------

function reducedMotion(): () => void {
  const original = window.matchMedia;
  window.matchMedia = ((query: string) => ({ matches: query.includes("reduce"), media: query, addEventListener: () => undefined,
    removeEventListener: () => undefined, onchange: null, addListener: () => undefined, removeListener: () => undefined,
    dispatchEvent: () => false })) as unknown as typeof window.matchMedia;
  return () => { window.matchMedia = original; };
}

async function answerRunTo(step: number, view: FigureViewDto, reads: Read[]) {
  await open({ ...view, predictions: [{ index: 0, prompt: "?", kind: "direction", answered: null, targetStep: step,
    choices: [{ value: "rises", label: "rises" }, { value: "falls", label: "falls" }, { value: "same", label: "same" }] }] }, logging(reads, []));
  await waitFor(() => expect(time()).toContain("t = 0 / 100"));
  api.readerFigurePredict.mockResolvedValue({ predictionId: "fp_1", figureId: "fig_review", extractionId: "ext_prob", predictionIndex: 0,
    learnerAnswer: "rises", matched: true, before: 1, after: 9, answer: "rises", explanationText: null });
  fireEvent.click(screen.getByLabelText("rises"));
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: FIGURE_COPY.answer })); });
  await waitFor(() => expect(time()).toContain(`t = ${step} / 100`));
}

it("writes a negative zero input as zero, as the sidecar now does", () => {
  expect(canonicalJson({ a: -0, b: 0, c: -1.5 })).toBe('{"a":0,"b":0,"c":-1.5}');
  expect(canonicalJson({ p: { a: -0 }, dt: 1 })).toBe('{"p":{"a":0},"dt":1}');
  // The verifier's program is canonical too: no -0 left for the page to read.
  expect(SIGNED_ZERO.program.parameters[0].default).toBe(0);
  expect(Object.is(SIGNED_ZERO.program.parameters[0].default, -0)).toBe(false);
});

it("plays the signed-zero program's prediction to the read that graded it, digest for digest", async () => {
  const restore = reducedMotion();
  try {
    const entry = SIGNED_ZERO.sketch.tested!.find((item) => item.values[0] === 0)!;
    expect(entry.steps).toContain(1);  // the graded step is a tested state
    const reads: Read[] = [];
    await answerRunTo(1, sketchView(SIGNED_ZERO.program, SIGNED_ZERO.sketch), reads);
    const atOne = reads.filter((read) => read.index === 1).pop()!;
    expect(atOne.digest).toBe(entry.digests[entry.steps.indexOf(1)]);
    fireEvent.keyDown(document.querySelector("[data-sketch-body]")!, { key: "t" });
    expect(document.querySelector('[data-sketch-probe="radius"]')!.textContent).toContain("9");  // as graded: rises, 1 -> 9
    expect(document.querySelector("[data-sketch-checks-withdrawn]")).toBeNull();
  } finally {
    restore();
  }
});

it("withdraws the checks when the read at a prediction's graded step differs from the one that graded it", async () => {
  const restore = reducedMotion();
  try {
    // What the old sidecar read at step 1 (it sent -0, so the program drew radius 1 there).
    const old = await newHost();
    old.load(SIGNED_ZERO.program.code.replace("!Object.is(p.a, -0)", "false"));
    old.init({ a: 0 }, 1);
    old.step({ a: 0 }, 1, 0, 1);
    const { sceneText, probesText } = old.readText({ a: 0 }, 1);
    expect(JSON.parse(probesText)).toEqual({ radius: 1 });
    const stale = sceneDigest(sceneText, probesText);
    const tested = SIGNED_ZERO.sketch.tested!.map((item) => item.values[0] === 0
      ? { ...item, digests: item.digests.map((digest, i) => (item.steps[i] === 1 ? stale : digest)) }
      : item);
    const reads: Read[] = [];
    await answerRunTo(1, sketchView(SIGNED_ZERO.program, { ...SIGNED_ZERO.sketch, tested }), reads);
    await waitFor(() => expect(document.querySelector("[data-sketch-checks-withdrawn]")).not.toBeNull());
    expect(badge()).toBe(SKETCH_FRAME.unchecked);
    expect(checkLines().some((line) => line.includes("radius of the drawn"))).toBe(false);
  } finally {
    restore();
  }
});
