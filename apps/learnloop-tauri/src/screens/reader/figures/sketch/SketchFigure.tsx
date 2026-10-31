// Reader RW5d P2: a sketch, open under its passage (spec_reader_show_me_figures_v1 §6.6, §9).
//
// The program runs in its sealed engine (a Web Worker in the app, through
// SketchRunnerContext); every result is validated (sketchScene.ts) before
// SketchSceneView draws it. The host owns every interaction: sliders and
// numeric fields from the declared parameters, draggable handles bound to
// them, "play" driving the program's clock (step buttons under reduced
// motion; nothing moves until pressed), "new sample" for a seeded program,
// and the values table (`t`, every declared value, paged). Changing a
// parameter or the seed restarts the run, so what is drawn is always "init,
// then n steps", the shape that was verified: every engine call goes through
// one queue, and each run carries a token no superseded call may commit under
// (Codex review F4). A prediction plays to exactly the step it is graded at
// (stepped through at once under reduced motion; Codex review F5). A call
// that outlives the watchdog pauses the sketch (the Worker is
// terminated); an error at the learner's settings says so and prefills
// "not right?" with code's words and the settings. The badge and the check
// lines are code-owned, worded here from closed fields; nothing the program
// draws can reach them. Nothing here takes focus or opens a modal.
//
// Fix round 4 (the independent sandbox review): a run is "a freshly loaded
// program, init, then the read schedule" (sketchScene.readSchedule, the
// verifier's read_steps): every scheduled step is read once, in order, and no
// other step is read, whatever the learner presses (play, step, a
// prediction's jump), so the page passes through the history verification
// checked even when a program changes its state when read. Every read's
// digest is compared with the verifier's at the states it tested (its
// parameters, the verified seed, a checked step); any difference withdraws
// the code-owned checks (checksWithdrawn.ts) and the sketch shows as an
// illustration. A prediction plays exactly the value it was graded at.
import { useCallback, useContext, useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";
import type { FigurePredictionDto, FigureSketchDto, FigureViewDto } from "../../../../api/dto";
import { COLOR, FONT_MONO } from "../../../../components/term";
import { logReaderAction } from "../../activity";
import { MeaningLabel, ModelVoice, SourceVoice } from "../../voices";
import { formatValue } from "../FigurePanels";
import { linkStyle, PredictionBlock, PredictionResult, prefersReducedMotion } from "../FigureInline";
import type { FiguresCtl } from "../useFigures";
import { SketchRunError, type Params } from "./sketchEngine";
import { SketchRunnerContext, withWatchdog, type SketchRunner } from "./sketchRunner";
import { SketchSceneView } from "./SketchScene";
import { clockSteps, probeProblems, readSchedule, sceneProblems, usableSchedule, type Scene, type SketchParameter, type SketchProbe, type SketchProgram } from "./sketchScene";
import { useChecksWithdrawn, withdrawChecks } from "./checksWithdrawn";

export const SKETCH_FRAME = {
  badge: "AI-written simulation · sandboxed · not checked against the book",
  unchecked: "AI-written simulation · nothing in it checked",
  notFromBooks: "AI-written simulation · sandboxed · not from your books",
  checksLead: "checked by LearnLoop:",
  withdrawn: "checks withdrawn: this run differs from the one LearnLoop checked, so nothing in it counts as checked",
} as const;

export const SKETCH_COPY = {
  howItRunsLink: "ⓘ how this runs",
  howItRuns:
    "Written by LearnLoop's model as a small program. It runs in a sealed sandbox inside LearnLoop: it can't see your files, your notes, the network or the rest of the app — it only computes what's drawn here.",
  paused: "paused — this simulation is too slow here",
  resume: "step ▸",
  error: "this simulation hit an error at these settings",
  newSample: "↻ new sample",
  play: "▸ play",
  stop: "■ stop",
  step: "step ▸",
  restart: "↺ restart",
  table: "t values as a table",
  notRight: "not right?",
  askBetter: "ask for a better version",
  notRightWhere: "Goes to the figure author with this version; the new version is checked like this one and this one is kept.",
  shows: "shows",
  assumes: "assumes",
  loading: "starting the simulation…",
} as const;

/** Whether a sketch's code-owned checks stand (fix round 4): it has checks, the verifier's digests to compare
 *  (a report without them predates the comparison: fail closed), and none of the page's reads disagreed. */
export function checksStand(sketch: FigureSketchDto | null | undefined, withdrawn = false): boolean {
  return !withdrawn && Boolean(sketch?.checks?.length) && Array.isArray(sketch?.tested) && sketch!.tested!.length > 0;
}

/** The badge slot for a sketch, from closed values only. */
export function sketchBadge(figure: Pick<FigureViewDto, "grounding" | "sketch">, withdrawn = false): string {
  if (figure.grounding === "none") return SKETCH_FRAME.notFromBooks;
  return checksStand(figure.sketch, withdrawn) ? SKETCH_FRAME.badge : SKETCH_FRAME.unchecked;
}

const quote = (name: string) => `‘${name}’`;

/** What a check speaks for when it covers one attribute of a drawn element (Codex review F3). */
export const ATTRIBUTE_WORDS: Record<string, string> = { y: "y values", values: "cell values", r: "radius" };

/** The check lines, worded by code from each check's closed fields (spec §9.5). */
export function sketchCheckLines(sketch: FigureSketchDto | null | undefined): string[] {
  if (!sketch) return [];
  const lines = sketch.checks.map((check) => {
    const parts: string[] = [];
    if (check.elements.length) parts.push(`the drawn ${check.elements.map(quote).join(", ")}`);
    for (const entry of check.partial ?? []) parts.push(`the ${ATTRIBUTE_WORDS[entry.attribute] ?? "values"} of the drawn ${quote(entry.element)}`);
    const plural = parts.length > 1 || check.elements.length > 1 || (check.partial ?? []).some((entry) => entry.attribute !== "r");
    const subject = parts.length ? parts.join(" and ") : `the value ${quote(check.probe)}`;
    const settings = `at ${check.settings} tested settings`;
    if (check.kind === "follows") return `${subject} ${plural ? "follow" : "follows"} ${check.statement} (AI-stated) ${settings}`;
    if (check.kind === "invariant") return `${subject} ${plural ? "are" : "is"} ${check.statement} ${settings}`;
    if (check.kind === "distribution") return `${subject} ${plural ? "agree" : "agrees"} with ${check.statement} (AI-stated) within sampling error ${settings}`;
    return `${subject} ${plural ? "are" : "is"} ${check.statement} (AI-stated) ${settings}`;
  });
  const unnamed = sketch.unnamedElements;
  if (sketch.notCovered.length || unnamed) {
    const named = sketch.notCovered.map(quote).join(", ");
    const others = unnamed ? `${named ? " and " : ""}${unnamed} other drawn element${unnamed === 1 ? "" : "s"}` : "";
    lines.push(`not covered: ${named}${others} (drawn, not checked)`);
  }
  return lines;
}

function defaultsOf(program: SketchProgram): Params {
  // + 0: a stored program from before verify round 2 may still say -0 (it is sent as 0 either way).
  return Object.fromEntries(program.parameters.map((parameter) => [parameter.name, Number(parameter.default) + 0]));
}

function clampStep(parameter: SketchParameter, raw: number): number {
  if (!Number.isFinite(raw)) return Number(parameter.default);
  const clamped = Math.min(parameter.max, Math.max(parameter.min, raw));
  const steps = Math.round((clamped - parameter.min) / parameter.step);
  return Math.min(parameter.max, Number((parameter.min + steps * parameter.step).toPrecision(12)));
}

function settingsText(params: Params): string {
  return Object.entries(params).map(([name, value]) => `${name}=${Number(value.toPrecision(6))}`).join(", ") || "the defaults";
}

/** keep (display): how many entries of a series or path the values table shows per page (Codex review F6). */
export const TABLE_PAGE = 50;

const num = (value: unknown) => formatValue(typeof value === "number" ? value : null);

/** One declared probe in the values table: a scalar as one value; a series
 *  or a path as every entry, a page at a time (index and value, or x and y). */
function ProbeEntries({ probe, value }: { probe: SketchProbe; value: unknown }) {
  const [page, setPage] = useState(0);
  if (probe.shape === "scalar") return <>{num(value)}</>;
  const entries = Array.isArray(value) ? value : [];
  const pages = Math.max(1, Math.ceil(entries.length / TABLE_PAGE));
  const current = Math.min(page, pages - 1);
  const first = current * TABLE_PAGE;
  const shown = entries.slice(first, first + TABLE_PAGE);
  const range = entries.length ? `${first + 1}–${first + shown.length} of ${entries.length}` : "none";
  const cell = { paddingRight: 12, textAlign: "right" as const };
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <table data-sketch-entries={probe.name} style={{ borderCollapse: "collapse" }}>
        <caption style={{ textAlign: "left", color: COLOR.textDim }}>
          {probe.shape === "pairs" ? "points" : "values"} {range}
        </caption>
        <thead>
          <tr>{probe.shape === "pairs"
            ? <><th scope="col" style={cell}>#</th><th scope="col" style={cell}>x</th><th scope="col" style={cell}>y</th></>
            : <><th scope="col" style={cell}>#</th><th scope="col" style={cell}>value</th></>}</tr>
        </thead>
        <tbody>
          {shown.map((entry, offset) => (
            <tr key={first + offset} data-sketch-entry={first + offset}>
              <td style={cell}>{first + offset}</td>
              {probe.shape === "pairs"
                ? <><td style={cell}>{num((entry as unknown[])?.[0])}</td><td style={cell}>{num((entry as unknown[])?.[1])}</td></>
                : <td style={cell}>{num(entry)}</td>}
            </tr>
          ))}
        </tbody>
      </table>
      {pages > 1 ? (
        <span style={{ display: "flex", gap: 10 }}>
          <button type="button" style={linkStyle} disabled={current === 0} data-sketch-page-previous={probe.name}
            onClick={() => setPage(Math.max(0, current - 1))}>◂ previous {TABLE_PAGE}</button>
          <button type="button" style={linkStyle} disabled={current >= pages - 1} data-sketch-page-next={probe.name}
            onClick={() => setPage(Math.min(pages - 1, current + 1))}>next {TABLE_PAGE} ▸</button>
        </span>
      ) : null}
    </div>
  );
}

/** keep (display): how often play advances (one scheduled read per tick; sketchEngine.PLAY_TICKS of them to t_max). */
const PLAY_MS = 60;

/** A random 32-bit seed for "new sample" (the host's, never the program's). */
function freshSeed(): number {
  const cryptoObject = (globalThis as { crypto?: Crypto }).crypto;
  if (cryptoObject?.getRandomValues) return cryptoObject.getRandomValues(new Uint32Array(1))[0];
  return Math.floor(Math.random() * 0xffffffff) >>> 0;
}

/** The step a prediction is graded at (the server's `targetStep`, shared with
 *  its verifier; computed the same way for a view that predates it). */
export function predictionTarget(program: SketchProgram, prediction: Pick<FigurePredictionDto, "index" | "targetStep">): number {
  if (typeof prediction.targetStep === "number") return prediction.targetStep;
  const total = clockSteps(program);
  const change = program.predictions?.[prediction.index]?.change ?? {};
  if ("run_to" in change && program.clock) return Math.min(total, Math.max(1, Math.round(change.run_to / program.clock.dt)));
  return total;
}

type RunState =
  | { kind: "loading" }
  | { kind: "ready" }
  | { kind: "paused" }
  | { kind: "error"; message: string; errorKind: string; params: Params };

export function SketchFigure({ figure, ctl, program }: { figure: FigureViewDto; ctl: FiguresCtl; program: SketchProgram }) {
  const factory = useContext(SketchRunnerContext);
  const [params, setParams] = useState<Params>(() => defaultsOf(program));
  const [seed, setSeed] = useState<number>(() => figure.sketch?.seed ?? 1);
  const [step, setStep] = useState(0);
  const [scene, setScene] = useState<Scene | null>(null);
  const [probes, setProbes] = useState<Record<string, unknown> | null>(null);
  const [state, setState] = useState<RunState>({ kind: "loading" });
  const [playing, setPlaying] = useState(false);
  const [showTable, setShowTable] = useState(false);
  const [showHow, setShowHow] = useState(false);
  const [noteOpen, setNoteOpen] = useState(false);
  const [note, setNote] = useState("");
  const [skipped, setSkipped] = useState(false);
  const [generation, setGeneration] = useState(0);
  const reduced = useMemo(prefersReducedMotion, []);
  const runner = useRef<SketchRunner | null>(null);
  const loaded = useRef<Promise<unknown> | null>(null);
  const busy = useRef(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  // Codex review F4: every engine call goes through one queue, in order, and
  // each run (an init at some parameters and seed) has a token; a call from a
  // superseded run never reads or commits. `at` is the run's own state: its
  // parameters and the step the engine is at.
  const queue = useRef<Promise<unknown>>(Promise.resolve());
  const runId = useRef(0);
  const at = useRef<{ params: Params; seed: number; step: number }>({ params, seed, step: 0 });
  // Codex review F5: the step playback stops at (a prediction's), and one a
  // restart should play to once its init is drawn.
  const target = useRef<number | null>(null);
  const pendingTarget = useRef<number | null>(null);
  const total = clockSteps(program);
  const names = useMemo(() => program.parameters.map((parameter) => parameter.name), [program]);
  // The read schedule: the verifier's, or computed the same way for a view without it.
  const schedule = useMemo(() => usableSchedule(figure.sketch?.readSteps, program) ?? readSchedule(program), [figure.sketch?.readSteps, program]);
  const withdrawn = useChecksWithdrawn(figure.figureId);
  const verifiedSeed = figure.sketch?.seed ?? 1;
  const tested = figure.sketch?.tested;

  const enqueue = useCallback(<T,>(operation: () => Promise<T>): Promise<T> => {
    const next = queue.current.then(operation, operation);
    queue.current = next.catch(() => undefined);
    return next;
  }, []);

  const stopPlay = useCallback(() => {
    if (timer.current) clearInterval(timer.current);
    timer.current = null;
    target.current = null;
    setPlaying(false);
  }, []);

  const fail = useCallback((caught: unknown, params: Params) => {
    stopPlay();
    if (caught instanceof SketchRunError && caught.kind === "paused") {
      setState({ kind: "paused" });
      return;
    }
    const message = caught instanceof Error ? caught.message : String(caught);
    const errorKind = caught instanceof SketchRunError ? caught.kind : "error";
    logReaderAction("sketch_error", { figure_id: figure.figureId, extraction_id: figure.extractionId, error_kind: errorKind });
    setState({ kind: "error", message, errorKind, params });
  }, [figure.figureId, figure.extractionId, stopPlay]);

  // One runner per open sketch (and per resume after a pause), disposed on close.
  useEffect(() => {
    const created = withWatchdog(factory(), undefined, () => {
      logReaderAction("sketch_paused", { figure_id: figure.figureId, extraction_id: figure.extractionId });
    });
    runner.current = created;
    loaded.current = created.load(program.code);
    return () => {
      if (timer.current) clearInterval(timer.current);
      runId.current += 1;  // nothing of this runner's commits after it is gone
      created.dispose();
      runner.current = null;
    };
  }, [factory, program.code, generation, figure.figureId, figure.extractionId]);

  /** At a state verification tested (its parameters, the verified seed, a checked step), the page's read
   *  must be the one it checked, digest for digest; on any difference the checks are withdrawn (fail closed). */
  const audit = useCallback((params: Params, seed: number, index: number, digest: string) => {
    if (!tested?.length || seed !== verifiedSeed) return;
    const entry = tested.find((item) => item.values.length === names.length && names.every((name, i) => item.values[i] === params[name]));
    const position = entry ? entry.steps.indexOf(index) : -1;
    if (!entry || position < 0 || entry.digests[position] === digest) return;
    withdrawChecks(figure.figureId);
  }, [tested, verifiedSeed, names, figure.figureId]);

  /** Read a step (a scheduled one) and validate it; commits nothing (the caller checks its run's token first). */
  const readChecked = useCallback(async (active: SketchRunner, params: Params, index: number, seed: number) => {
    const result = await active.read(params, index);
    audit(params, seed, index, result.digest);
    const sceneIssues = sceneProblems(result.scene, names);
    if (sceneIssues.length) throw new SketchRunError("scene", `the scene ${sceneIssues[0]}`);
    const probeIssues = probeProblems(result.probes, program.probes);
    if (probeIssues.length) throw new SketchRunError("probe", probeIssues[0]);
    return { scene: result.scene as Scene, probes: result.probes as Record<string, unknown> };
  }, [names, program.probes, audit]);

  const commit = useCallback((id: number, read: { scene: Scene; probes: Record<string, unknown> }, index: number) => {
    if (id !== runId.current) return false;
    at.current = { ...at.current, step: index };
    setScene(read.scene);
    setProbes(read.probes);
    setStep(index);
    return true;
  }, []);

  /** Step the current run toward `end` through at most `reads` scheduled steps, reading each one it reaches
   *  (every scheduled step once, no other), then commit the last read (queued). */
  const advanceRun = useCallback(async (id: number, active: SketchRunner, end: number, reads: number) => {
    if (id !== runId.current || !program.clock) return;
    const { params: runParams, seed: runSeed, step: from } = at.current;
    if (from >= end) return;
    let reached = from;
    let done = 0;
    let last: { scene: Scene; probes: Record<string, unknown> } | null = null;
    while (reached < end && done < reads) {
      const next = Math.min(end, schedule.find((step) => step > reached) ?? end);
      await active.step(runParams, program.clock.dt, reached, next - reached);
      if (id !== runId.current) return;
      reached = next;
      at.current = { ...at.current, step: reached };
      last = await readChecked(active, runParams, reached, runSeed);
      if (id !== runId.current) return;
      done += 1;
    }
    if (last) commit(id, last, reached);
  }, [program.clock, schedule, readChecked, commit]);

  /** One play tick or step press: toward the prediction's target if one is set, else t_max. */
  const advance = useCallback(async () => {
    const active = runner.current;
    if (!active || busy.current || !program.clock) return;
    const id = runId.current;
    busy.current = true;
    try {
      await enqueue(async () => {
        const end = Math.min(total, target.current ?? total);
        if (id === runId.current && at.current.step >= end) {
          stopPlay();
          return;
        }
        await advanceRun(id, active, end, 1);
        if (id === runId.current && at.current.step >= end) stopPlay();
      });
    } catch (caught) {
      if (id === runId.current) fail(caught, at.current.params);
    } finally {
      if (id === runId.current) busy.current = false;
    }
  }, [program.clock, total, enqueue, advanceRun, stopPlay, fail]);
  const advanceRef = useRef(advance);
  advanceRef.current = advance;

  const playTo = useCallback((end: number) => {
    if (timer.current) clearInterval(timer.current);
    target.current = end;
    setPlaying(true);
    timer.current = setInterval(() => { void advanceRef.current(); }, PLAY_MS);
  }, []);

  // Restart the run whenever the parameters or the seed change: init (on a
  // freshly loaded program), then read step 0 (and play on to a prediction's
  // step, if one is pending).
  useEffect(() => {
    const active = runner.current;
    const ready = loaded.current;
    if (!active || !ready) return;
    runId.current += 1;
    const id = runId.current;
    const runParams = params;
    const goal = pendingTarget.current;
    pendingTarget.current = null;
    busy.current = true;
    enqueue(async () => {
      await ready;
      if (id !== runId.current) return;
      await active.init(runParams, seed);
      if (id !== runId.current) return;
      at.current = { params: runParams, seed, step: 0 };
      const read = await readChecked(active, runParams, 0, seed);
      if (!commit(id, read, 0)) return;
      setState({ kind: "ready" });
      if (goal && program.clock) {
        if (reduced) await advanceRun(id, active, goal, Number.POSITIVE_INFINITY);  // straight to it, no motion (every scheduled step still read)
        else playTo(goal);
      }
    })
      .catch((caught) => { if (id === runId.current) fail(caught, runParams); })
      .finally(() => { if (id === runId.current) busy.current = false; });
  }, [params, seed, generation, enqueue, readChecked, commit, advanceRun, playTo, reduced, program.clock, fail]);

  useEffect(() => () => { if (timer.current) clearInterval(timer.current); }, []);

  const play = () => {
    if (playing) {
      stopPlay();
      return;
    }
    if (at.current.step >= total) {
      // At t_max: play starts over (the run restarts at step 0; press again to play).
      setParams((current) => ({ ...current }));
      return;
    }
    logReaderAction("figure_animated", { figure_id: figure.figureId, extraction_id: figure.extractionId, parameter: "t" });
    playTo(total);
  };

  const setParam = (name: string, raw: number) => {
    const parameter = program.parameters.find((item) => item.name === name);
    if (!parameter) return;
    stopPlay();
    setParams((current) => (current[name] === clampStep(parameter, raw) ? current : { ...current, [name]: clampStep(parameter, raw) }));
  };

  const onHandle = (id: string, x: number, y: number) => {
    const handle = scene?.elements.find((element) => element.type === "handle" && element.id === id);
    if (!handle || handle.type !== "handle") return;
    if (handle.binds.x) setParam(handle.binds.x, x);
    if (handle.binds.y) setParam(handle.binds.y, y);
  };

  /** After an answer, show what was graded (Codex review F5): the verifier's
   *  run (the defaults with the change, the verified seed) from init to the
   *  prediction's step, stopping exactly there. The change is set exactly as
   *  graded (the independent sandbox review, finding 2: validation requires
   *  a value the controls can be set to, so nothing is re-snapped here). */
  const applyPrediction = (prediction: FigurePredictionDto) => {
    const change = program.predictions?.[prediction.index]?.change ?? {};
    stopPlay();
    pendingTarget.current = predictionTarget(program, prediction);
    setSeed(figure.sketch?.seed ?? 1);
    setParams(() => {
      const next = defaultsOf(program);
      for (const [name, value] of Object.entries(change)) {
        const parameter = program.parameters.find((item) => item.name === name);
        const exact = Number(value) + 0;
        if (parameter) next[name] = Number.isFinite(exact) && exact >= parameter.min && exact <= parameter.max ? exact : clampStep(parameter, exact);
      }
      return next;
    });
  };

  const resume = () => {
    setState({ kind: "loading" });
    setGeneration((value) => value + 1);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const target = event.target as HTMLElement;
    if (["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName) && (target as HTMLInputElement).type !== "range") return;
    if (event.key === "t" && !event.ctrlKey && !event.metaKey && !event.altKey) {
      event.preventDefault();
      setShowTable((value) => !value);
    }
  };

  const openPrediction = ctl.contract?.predictions && !skipped
    && !figure.predictions.some((prediction) => prediction.answered !== null) ? figure.predictions[0] ?? null : null;
  const answeredPrediction = figure.predictions.find((prediction) => prediction.answered !== null) ?? null;
  const locked = openPrediction !== null;
  const stands = checksStand(figure.sketch, withdrawn);
  const checkLines = stands ? sketchCheckLines(figure.sketch) : [];
  const withdrawnShown = !stands && Boolean(figure.sketch?.checks?.length);
  const prefill = state.kind === "error" ? `${SKETCH_COPY.error}: ${settingsText(state.params)} (${state.message})`.slice(0, 600) : "";

  return (
    <div data-sketch-body="" onKeyDown={onKeyDown} style={{ display: "flex", flexDirection: "column", gap: 8, border: `1px solid ${COLOR.border}`, padding: "8px 10px", background: COLOR.bgElev }}>
      {figure.demonstrates ? <ModelVoice first note={SKETCH_COPY.shows}>{figure.demonstrates}</ModelVoice> : null}
      {figure.assumptions?.length ? (
        <div data-figure-assumptions="" style={{ display: "flex", flexDirection: "column", gap: 3 }}>
          <MeaningLabel>{SKETCH_COPY.assumes} · AI-written</MeaningLabel>
          {figure.assumptions.map((assumption, index) => (
            <div key={index} style={{ display: "flex", flexDirection: "column", gap: 2 }}>
              <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text }}><span aria-hidden="true">◇ </span>{assumption.text}</span>
              {assumption.quote ? <SourceVoice><span>{assumption.quote}</span></SourceVoice> : null}
            </div>
          ))}
        </div>
      ) : null}
      {openPrediction ? (
        <PredictionBlock figure={figure} prediction={openPrediction} ctl={ctl}
          onApplied={() => applyPrediction(openPrediction)} onSkip={() => setSkipped(true)} />
      ) : null}
      {answeredPrediction && !openPrediction ? (
        <PredictionResult figure={figure} prediction={answeredPrediction} ctl={ctl} format="number" />
      ) : null}
      {program.parameters.length ? (
        <div data-sketch-controls="" style={{ display: "flex", gap: 16, flexWrap: "wrap", alignItems: "center" }}>
          {program.parameters.map((parameter) => {
            const value = params[parameter.name] ?? parameter.default;
            return (
              <span key={parameter.name} style={{ display: "inline-flex", gap: 6, alignItems: "center", fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text }}>
                <label style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
                  {parameter.label}
                  <input type="range" min={parameter.min} max={parameter.max} step={parameter.step} value={value} disabled={locked}
                    aria-label={parameter.label} onChange={(event) => setParam(parameter.name, Number(event.target.value))} />
                </label>
                <input type="number" min={parameter.min} max={parameter.max} step={parameter.step} value={Number(value.toPrecision(6))}
                  disabled={locked} aria-label={`${parameter.label} value`} onChange={(event) => setParam(parameter.name, Number(event.target.value))}
                  style={{ width: 70, fontFamily: FONT_MONO, fontSize: 11, background: COLOR.bgInput, color: COLOR.text, border: `1px solid ${COLOR.border}` }} />
              </span>
            );
          })}
        </div>
      ) : null}
      <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "baseline", fontFamily: FONT_MONO, fontSize: 11 }}>
        {program.clock ? (
          reduced ? (
            <button type="button" style={linkStyle} disabled={locked || state.kind !== "ready"} data-sketch-step="" onClick={() => void advance()}>{SKETCH_COPY.step}</button>
          ) : (
            <button type="button" style={linkStyle} disabled={locked || state.kind !== "ready"} data-sketch-play="" onClick={play}>{playing ? SKETCH_COPY.stop : SKETCH_COPY.play}</button>
          )
        ) : null}
        {program.clock ? <span data-sketch-time="" style={{ color: COLOR.textDim }}>t = {formatValue(step * program.clock.dt)} / {formatValue(program.clock.t_max)}</span> : null}
        {program.clock && step > 0 ? <button type="button" style={linkStyle} onClick={() => { stopPlay(); setParams((current) => ({ ...current })); }}>{SKETCH_COPY.restart}</button> : null}
        {program.seeded ? (
          <button type="button" style={linkStyle} disabled={locked} data-sketch-new-sample="" onClick={() => { stopPlay(); setSeed(freshSeed()); }}>{SKETCH_COPY.newSample}</button>
        ) : null}
        <button type="button" style={linkStyle} aria-expanded={showHow} onClick={() => setShowHow((value) => !value)}>{SKETCH_COPY.howItRunsLink}</button>
      </div>
      {showHow ? <span data-sketch-how=""><MeaningLabel>{SKETCH_COPY.howItRuns}</MeaningLabel></span> : null}
      {state.kind === "paused" ? (
        <div data-sketch-paused="" style={{ display: "flex", gap: 10, alignItems: "baseline" }}>
          <MeaningLabel>{SKETCH_COPY.paused}</MeaningLabel>
          <button type="button" style={linkStyle} onClick={resume}>{SKETCH_COPY.resume}</button>
        </div>
      ) : null}
      {state.kind === "error" ? (
        <div data-sketch-error={state.errorKind} style={{ display: "flex", gap: 10, alignItems: "baseline", flexWrap: "wrap" }}>
          <MeaningLabel style={{ color: COLOR.red }}>{SKETCH_COPY.error} ({settingsText(state.params)})</MeaningLabel>
          {ctl.contract?.revisions ? (
            <button type="button" style={linkStyle} data-sketch-error-not-right="" onClick={() => { setNote(prefill); setNoteOpen(true); }}>{SKETCH_COPY.notRight}</button>
          ) : null}
        </div>
      ) : null}
      {state.kind === "loading" && !scene ? <MeaningLabel>{SKETCH_COPY.loading}</MeaningLabel> : null}
      {scene && state.kind !== "error" ? <SketchSceneView scene={scene} onHandle={locked ? undefined : onHandle} label={figure.demonstrates ?? undefined} /> : null}
      {showTable && probes ? (
        <table data-sketch-values="" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text, borderCollapse: "collapse" }}>
          <thead>
            <tr><th style={{ textAlign: "left", paddingRight: 12 }}>value</th><th style={{ textAlign: "left" }}>at t = {program.clock ? formatValue(step * program.clock.dt) : "—"}</th></tr>
          </thead>
          <tbody>
            {program.probes.map((probe) => (
              <tr key={probe.name} data-sketch-probe={probe.name} style={{ verticalAlign: "top" }}>
                <th scope="row" style={{ paddingRight: 12, fontStyle: "italic", fontWeight: "normal", textAlign: "left", color: COLOR.textItalic }}>{probe.label}</th>
                <td><ProbeEntries probe={probe} value={probes[probe.name]} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
      {withdrawnShown ? (
        <span data-sketch-checks-withdrawn=""><MeaningLabel style={{ fontSize: 11 }}>{SKETCH_FRAME.withdrawn}</MeaningLabel></span>
      ) : null}
      {checkLines.length ? (
        <div data-sketch-checks="" style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {figure.sketch?.checks.length ? <MeaningLabel style={{ fontSize: 11 }}>{SKETCH_FRAME.checksLead}</MeaningLabel> : null}
          {checkLines.map((line, index) => (
            <span key={index} data-sketch-check-line="" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>· {line}</span>
          ))}
        </div>
      ) : null}
      {program.annotations?.length ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {program.annotations.map((annotation, index) => (
            <MeaningLabel key={index} style={{ fontSize: 11 }}>◇ {annotation.target}: {annotation.text}</MeaningLabel>
          ))}
        </div>
      ) : null}
      <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "baseline" }}>
        <button type="button" style={linkStyle} aria-pressed={showTable} onClick={() => setShowTable((value) => !value)}>{SKETCH_COPY.table}</button>
        {ctl.contract?.revisions ? (
          noteOpen ? (
            <form onSubmit={(event) => { event.preventDefault(); ctl.revise(figure, note); setNoteOpen(false); setNote(""); }}
              style={{ display: "flex", gap: 6, alignItems: "baseline", flexWrap: "wrap" }}>
              <input value={note} onChange={(event) => setNote(event.target.value)} maxLength={600} aria-label={SKETCH_COPY.notRight}
                data-sketch-note=""
                style={{ fontFamily: FONT_MONO, fontSize: 11, width: 360, background: COLOR.bgInput, color: COLOR.text, border: `1px solid ${COLOR.border}` }} />
              <button type="submit" style={linkStyle}>{SKETCH_COPY.askBetter}</button>
              <MeaningLabel>{SKETCH_COPY.notRightWhere}</MeaningLabel>
            </form>
          ) : (
            <button type="button" style={linkStyle} onClick={() => setNoteOpen(true)}>{SKETCH_COPY.notRight}</button>
          )
        ) : null}
        {figure.versions > 1 ? <MeaningLabel>version {figure.versions}</MeaningLabel> : null}
      </div>
    </div>
  );
}
